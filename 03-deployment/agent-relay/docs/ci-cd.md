# CI/CD

## Workflow

`.github/workflows/ci.yml` (repo root, since GitHub only discovers workflows
there) has three jobs, chained with `needs:` so a failure stops the rest:

1. `test` — spins up a Postgres 16 service container, runs the starter's
   protocol tests (`test_agent_relay.py`) against it, then starts the API
   itself against that same Postgres instance and runs the live integration
   test (`tests/integration/test_integration_live.py`) against it.
2. `build` — only runs if `test` passes. Builds the Docker image, tagged
   `<short-sha>-<epoch-timestamp>` (e.g. `agent-relay:a1b2c3d-1758319200`).
   The timestamp suffix keeps the tag unique across repeated `act` runs of
   the same commit — the short SHA alone ties the image to a commit but
   would collide on a second local run of that commit without it.
3. `deploy` — only runs if `build` passes. Loads the tagged image into the
   existing `agent-relay` kind cluster (from Q5), applies `k8s/`, then
   `kubectl set image`s the Deployment and waits on `kubectl rollout status`
   to confirm the new pod comes up ready.

If `test` fails, GitHub Actions' `needs:` dependency skips `build` and
`deploy` automatically — the currently deployed version is left running
untouched, which is the required fail-closed behavior for Q6.

`deploy` installs `kubectl` via `azure/setup-kubectl` and the `kind` CLI via
`helm/kind-action` with `install_only: true`. That input matters: without
it, `helm/kind-action` runs `kind create cluster` and would spin up a brand
new cluster every invocation instead of reusing the persistent `agent-relay`
cluster from Q5 (its default use case is an ephemeral cluster for chart
testing, not deploying onto one that already exists).

Trigger is `workflow_dispatch` only — no `push`/`pull_request`. `deploy`
targets a kind cluster that only exists on your machine, so this workflow
only makes sense run locally via `act`; it would fail at the `kind load`
step on GitHub's hosted runners, which have no such cluster.

## Running it locally with `act`

The `deploy` job needs two things a plain `act` invocation doesn't provide:
the host's Docker daemon (so `docker build`/`kind load` act on the same kind
cluster your shell sees) and a kubeconfig that resolves inside act's job
containers. Everything below runs on your host — nothing here runs from
this dev container.

**Don't pass a custom `--network`.** An earlier version of this doc used
`--network kind` so job containers could resolve the kind control-plane
container by name. That breaks the `test` job: act normally makes service
containers (Postgres here) reachable at `localhost` by sharing a network
namespace between the job and its services, and a custom `--network`
overrides that, leaving `localhost:5432` unreachable
(`connection refused`). Use `host.docker.internal` instead, which Docker
Desktop resolves from inside any container regardless of which network it's
on, and leave the default networking alone so Postgres keeps working at
`localhost`.

1. **Mount the host's Docker socket** so `docker build`/`kind load` act on
   the same kind cluster your shell sees:

   ```bash
   act workflow_dispatch \
     --container-daemon-socket /var/run/docker.sock
   ```

2. **Point a kubeconfig at the host instead of `127.0.0.1`** — the default
   `~/.kube/config` kind writes points at `127.0.0.1`, which only resolves
   from the host itself, not from inside another container:

   ```bash
   kind get kubeconfig --name agent-relay > /tmp/kind-kubeconfig-host.yaml
   sed -i '' 's/127.0.0.1/host.docker.internal/' /tmp/kind-kubeconfig-host.yaml
   ```

   (drop the `''` after `-i` if you're on Linux/GNU sed instead of macOS)

3. **Run it, mounting that kubeconfig in:**

   ```bash
   act workflow_dispatch \
     -P ubuntu-latest=catthehacker/ubuntu:act-latest \
     --container-daemon-socket /var/run/docker.sock \
     --container-options "-v /tmp/kind-kubeconfig-host.yaml:/root/.kube/config"
   ```

4. Stop `docker compose` first if it's still running — it holds host port
   8000, which the deployed dashboard also wants once you port-forward to
   it.

## Verifying a run

After a green `act` run:

```bash
kubectl port-forward svc/agent-relay 8000:8000
```

Repeat the Q2 flow (`SPEC.md` scenario 1), or the live integration test
against `http://localhost:8000`, exactly as the manual verification in
`docs/deployment.md`.

## Demonstrating the fail-closed behavior

Break a test on purpose (e.g. flip an assertion in `test_agent_relay.py`),
run the workflow, and confirm: `test` fails red, `build` and `deploy` show
as skipped, and the already-deployed pod and dashboard are untouched.

## v2 heading demo

To exercise the full loop end-to-end: change the `<h1>` in `dashboard.html`
from `Agent Relay` to `Agent Relay v2`, commit, and run the workflow again.
Once `deploy` finishes, port-forward and refresh the dashboard — the new
heading confirms the pipeline actually shipped the new image and rolled the
Deployment.
