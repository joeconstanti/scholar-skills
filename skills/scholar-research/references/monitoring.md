# Repeat monitoring

Use a stable run definition: fixed query matrix, platform list, geography, language, sampling depth, and observation cadence. Save each observation as a new record or run rather than overwriting historical metrics.

Keep raw evidence immutable. Derive normalized datasets and reports from it so scoring changes can be reproduced. Cache successful fetches where freshness permits, checkpoint after each platform, and make collection idempotent by canonical URL plus observation time.

Set explicit limits for runtime, pages or items per platform, concurrency, retry count, and backoff. Stop a source after repeated throttling or denial and record the reason. Long-running does not mean unbounded.

Compare each platform to its own prior samples. Alert on material changes in velocity, breadth, or theme composition, not merely on one viral item. Periodically revisit queries because vocabulary drifts, but version query changes so apparent growth is not confused with expanded collection.
