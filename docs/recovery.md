# Failure, retry, and recovery

Only errors explicitly classified as retryable receive one automatic retry. The same adapter call and unchanged profile are used. A second failure stops the pipeline and creates a diagnostic package. Validation failures are fatal and are not automatically retried.

Cancellation is cooperative between stages. The application does not kill a project save or raster export in progress.

Resume is conservative. Persisted `last_successful_stage` must agree with inspected project evidence from the adapter. Completed/output stages require fresh output validation and are not automatically resumed. Existing output always needs an explicit policy; perfect recovery after arbitrary crashes is not promised.
