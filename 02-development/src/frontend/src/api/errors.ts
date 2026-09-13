// Shared between the mock and HTTP implementations so callers only ever
// import one error type regardless of which client is active.
export class ApiRequestError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}
