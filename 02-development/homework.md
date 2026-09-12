## Question 0: Pick your project

Which project did you choose for this homework?

> 💡 **Answer:** Restaurant waitlist manager

## Question 1: Spec first

Open a chat assistant and ask it to help you come up with the specification.

Also ask it to help you come up with the name for this application. What's the name you chose?

> 💡 **Answer:**

## Question 2: GitHub Repository

Create a new GitHub repository (or a folder in the repository you used for Homework 1), clone it locally. Put the spec there.

Commit and push. What's the sha1 hash for this commit?

> 💡 **Answer:**

## Question 3: Frontend prototype

Build a frontend prototype with a mocked backend. To make it simpler, use your coding agent directly, not Lovable (but you can experiment with it too).

Implement the frontend for the app described in _docs/specs.md. Put it in frontent/.

Don't implement the backend yet. Centralize all the backend calls
in one place and mock them for now.

Make the UI interactive so I can use the main features from the spec.
Iterate until you like the results.

Which command do you use to start the frontend?

> 💡 **Answer:**

## Question 4: Backend

Now let's create the backend. You can first ask your coding assistant to analyze the frontend code and create the specs, and then based on specs create the backend. Or you can create backend directly.

Like in the lessons, we'll first create the backend with a mock database, make sure it integrates well with the frontend, and then replace it with a real database.

Your prompt may look like this:

Based on openapi.yaml, create a FastAPI backend. Use uv for package management.
Use a mock database, we will replace it with a real one later.
Write tests for the endpoints first, then implement them.
Which command do you use to start the backend?

> 💡 **Answer:**

## Question 5: Connect frontend and backend

The backend now works (presumably) so let's connect frontent to it. Ask the coding assistant to do it.

You can verify that the connection works manually, but you can also ask your agent to use the browser to check it for you.

Which URL does the frontend use to talk to the backend?

> 💡 **Answer:**

## Question 6: Database

Now the backend and frontend work fine, you can swap the mock store for a real database.

Keep the app database-agnostic and use SQLAlchemy for that.

Make sure test still pass and add more tests if needed. Ask your agent for recommendations.

Which command do you use for running tests?

> 💡 **Answer:**