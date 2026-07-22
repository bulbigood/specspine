# Error handling

Owns centralized conversion of application failures into stable HTTP error responses.

Controllers forward failures through the shared asynchronous and error middleware boundary instead of defining endpoint-specific error formats.
