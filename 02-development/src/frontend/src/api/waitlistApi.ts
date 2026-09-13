// Single point of contact between the UI and the backend (docs/spec.md
// 6.2). Everything else in the app imports `waitlistApi` from here and
// never talks to the network or the mock store directly — swapping
// implementations only ever touches this file's two backing modules.
//
// VITE_USE_MOCK=true forces the in-memory mock even when a backend is
// running (handy for frontend-only work); it defaults to the real backend.

import { httpWaitlistApi } from "./httpWaitlistApi";
import { mockWaitlistApi } from "./mockWaitlistApi";

export { ApiRequestError } from "./errors";

const useMock = import.meta.env.VITE_USE_MOCK === "true";

export const waitlistApi = useMock ? mockWaitlistApi : httpWaitlistApi;
