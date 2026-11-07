# Evaluation: extended.json

34/50 passed. Answer correctness: 34/50. Routing: 34/50. Limited narrative checks: 4 cases, 1 failures. Unchecked prose is not certified. Model: `gemini-3.1-flash-lite`. Cache disabled. Trials: 1.

| Trial | ID | Strict pass | Answer | Routing | Narrative | Failure |
|---|---|---|---|---|---|---|
| 1 | ext-01 | True | True | True | not_checked |  |
| 1 | ext-02 | True | True | True | passed |  |
| 1 | ext-03 | True | True | True | passed |  |
| 1 | ext-04 | True | True | True | not_checked |  |
| 1 | ext-05 | True | True | True | not_checked |  |
| 1 | ext-06 | True | True | True | not_checked |  |
| 1 | ext-07 | True | True | True | not_checked |  |
| 1 | ext-08 | True | True | True | not_checked |  |
| 1 | ext-09 | True | True | True | not_checked |  |
| 1 | ext-10 | True | True | True | not_checked |  |
| 1 | ext-11 | True | True | True | not_checked |  |
| 1 | ext-12 | True | True | True | not_checked |  |
| 1 | ext-13 | True | True | True | not_checked |  |
| 1 | ext-14 | True | True | True | not_checked |  |
| 1 | ext-15 | True | True | True | not_checked |  |
| 1 | ext-16 | True | True | True | not_checked |  |
| 1 | ext-17 | True | True | True | not_checked |  |
| 1 | ext-18 | True | True | True | not_checked |  |
| 1 | ext-19 | True | True | True | not_checked |  |
| 1 | ext-20 | True | True | True | not_checked |  |
| 1 | ext-21 | True | True | True | passed |  |
| 1 | ext-22 | True | True | True | not_checked |  |
| 1 | ext-23 | True | True | True | not_checked |  |
| 1 | ext-24 | True | True | True | not_checked |  |
| 1 | ext-25 | True | True | True | not_checked |  |
| 1 | ext-26 | True | True | True | not_checked |  |
| 1 | ext-27 | True | True | True | not_checked |  |
| 1 | ext-28 | True | True | True | not_checked |  |
| 1 | ext-29 | True | True | True | not_checked |  |
| 1 | ext-30 | True | True | True | not_checked |  |
| 1 | ext-31 | True | True | True | not_checked |  |
| 1 | ext-32 | True | True | True | not_checked |  |
| 1 | ext-33 | True | True | True | not_checked |  |
| 1 | ext-34 | True | True | True | not_checked |  |
| 1 | ext-35 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator']; got []. / result: Reference 0: No successful tool evidence. |
| 1 | ext-36 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator']; got []. / result: Reference 0: No successful tool evidence. |
| 1 | ext-37 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator']; got []. / result: Reference 0: No successful tool evidence. |
| 1 | ext-38 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator']; got []. / result: Reference 0: No successful tool evidence. |
| 1 | ext-39 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator']; got []. / result: Reference 0: No successful tool evidence. |
| 1 | ext-40 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator']; got []. / result: Reference 0: No successful tool evidence. |
| 1 | ext-41 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator']; got []. / result: Reference 0: No successful tool evidence. |
| 1 | ext-42 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator']; got []. / result: Reference 0: No successful tool evidence. |
| 1 | ext-43 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator']; got []. / result: Reference 0: No successful tool evidence. |
| 1 | ext-44 | False | False | False | failed | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator', 'sql_query']; got []. / result: Reference 0: No successful tool evidence. / Reference 1: No successful tool evidence. / faithfulness: numeric_claim_present: expected 185.5, actual [429.0] |
| 1 | ext-45 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator', 'sql_query']; got []. / result: Reference 0: No successful tool evidence. / Reference 1: No successful tool evidence. |
| 1 | ext-46 | False | False | False | not_checked | status: Expected answer; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools ['exposure_calculator', 'sql_query']; got []. / result: Reference 0: No successful tool evidence. / Reference 1: No successful tool evidence. |
| 1 | ext-47 | False | False | False | not_checked | status: Expected clarification; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools []; got []. |
| 1 | ext-48 | False | False | False | not_checked | status: Expected clarification; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools []; got []. |
| 1 | ext-49 | False | False | False | not_checked | status: Expected unsupported; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools []; got []. |
| 1 | ext-50 | False | False | False | not_checked | status: Expected unsupported; actual error: Gemini request failed (ClientError, status=429). Check model availability, credentials, network, and quota. / routing: Expected tools []; got []. |
