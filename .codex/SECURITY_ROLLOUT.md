# HTTPS hardening rollout

This change is prepared for review. It has not been deployed.

## Release prerequisite

Reconcile this repository with the currently deployed source before deploying.
The public production API exposes Koki routes which are absent from this checkout.
Do not deploy the current main branch over that newer deployment or use a moving
`latest` image as a rollback reference.

## Change scope

- Production Django CSRF and session cookies default to `Secure`; local
  `DEBUG=True` development remains usable over HTTP.
- The nginx image changes to the official `1.30.6-alpine` stable security release.
- nginx stops advertising its version and sends a five-minute, host-only HSTS
  header on HTTPS responses. There is no `includeSubDomains` or preload policy.
- Existing API routes, bearer authentication, CORS, webhook processing, database
  schema, worker behavior, and client messaging are not changed by this patch.

## Validation and deployment

1. Record the current backend and nginx image digests and preserve the deployed
   compose file, nginx configuration, and application source. Keep environment
   secrets on the server. Verify a current database backup.
2. Apply these small changes to the reconciled source and run the security tests
   plus the existing application tests in an isolated environment.
3. In staging, validate the compose configuration and run `nginx -t` using the
   exact candidate image, configuration, certificate mount, and Docker network.
   A Docker runtime was unavailable during local preparation, so this nginx
   runtime validation remains required.
4. Confirm admin login and CSRF-protected POSTs work over HTTPS; verify both
   cookies have `Secure`. Confirm the existing Koki endpoints retain their
   authorization checks and integrations retain their existing behavior.
5. Deploy the reconciled backend with an immutable image reference using the
   established deployment process. Pre-pull the nginx image before the rollout.
   Recreating a single nginx container can briefly interrupt connections; use
   an agreed maintenance window or a tested rolling arrangement.
6. Check the public health endpoint, admin login, authorization failures, current
   Koki routes, HTTPS redirect, and response headers after rollout. Do not send
   client messages or create bookings as a smoke test.

## Rollback

Restore the recorded image digests and configuration through the same deployment
process. Do not restore an older database for this configuration-only change.
If HSTS must be withdrawn, serve `Strict-Transport-Security: max-age=0` over HTTPS;
clients otherwise retain the short policy for at most five minutes after their
last response containing it.

## Sources

- https://docs.djangoproject.com/en/6.0/ref/settings/#csrf-cookie-secure
- https://docs.djangoproject.com/en/6.0/ref/settings/#session-cookie-secure
- https://nginx.org/en/security_advisories.html
- https://github.com/docker-library/official-images/blob/master/library/nginx
