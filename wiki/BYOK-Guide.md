# BYOK Guide

Bring Your Own Key (BYOK) lets a caller select an AI provider for an active
Trinity tool without changing the hosted server's default routing.

## Read live routing first

Provider catalogues and model IDs expire. Before configuring BYOK, check:

- [`/health`](https://verifimind.ysenseai.org/health) for hosted per-stage
  routing, catalogue freshness, construction fallback, and runtime-failover
  state;
- [`/setup`](https://verifimind.ysenseai.org/setup) for current provider
  configuration;
- the [server card](https://verifimind.ysenseai.org/.well-known/mcp/server-card.json)
  for live discovery;
- [Current Production Status](Current-Production-Status) for the deployed
  release boundary.

Do not choose a model from an old Wiki table.

## Supported provider classes

The current remote BYOK catalogue has six providers:

| Provider | Provider ID |
|---|---|
| Google Gemini | `gemini` |
| Anthropic | `anthropic` |
| OpenAI | `openai` |
| Groq | `groq` |
| Cerebras | `cerebras` |
| Mistral | `mistral` |

`ollama` is a separate local/self-hosted provider. It works only when the server
process can reach the caller-managed Ollama service; the public hosted service
cannot use an Ollama process running on your laptop.

**xAI is not part of the current provider catalogue.**

Use the model catalogue reported by the live service. The server applies a
freshness contract to the six remote catalogues, but provider-side availability
can still change between verifications.

## Three routing modes

### 1. Hosted routing

With no BYOK parameters, the hosted service selects its configured provider for
each X, Z, and CS stage. The three stages are not guaranteed to use three
different providers or model families.

### 2. Global BYOK

Pass `llm_provider` and `api_key` to an active Trinity tool. For
`run_full_trinity`, the global pair applies to all stages unless a per-stage
override is present.

Example request in natural language:

> Use `run_full_trinity` with my Groq provider credentials. Keep
> `save_to_history=false` and report the provider/model and quality marker for
> every stage.

### 3. Per-stage BYOK

`run_full_trinity` also accepts:

- `x_provider` + `x_api_key`
- `z_provider` + `z_api_key`
- `cs_provider` + `cs_api_key`

Per-stage values take precedence over the global pair. This lets a caller
deliberately select different providers, but diversity should be verified from
the returned stage metadata rather than assumed from configuration intent.

## Key handling

- Keys are request-scoped and are not intentionally stored as account data.
- Provider failures are logged without raw keys or raw SDK response bodies.
- The selected provider receives the prompt, optional context, and any prior
  stage output needed for that inference.
- Provider processing remains governed by that provider's terms, region,
  retention settings, and the caller's account agreement.
- Never put a key in a prompt, tracked file, issue, discussion, screenshot, or
  shared transcript.
- Prefer an explicit provider ID. Key-prefix detection is convenience behavior,
  not a durable integration contract.

Read the live [Privacy Policy](https://verifimind.ysenseai.org/privacy) before
sending personal, confidential, regulated, or third-party data.

## Failure and fallback semantics

Keep these mechanisms separate:

1. **Construction fallback** chooses a provider only when the configured hosted
   provider cannot be constructed.
2. **Runtime failover** would move an in-flight stage between providers only
   when the separately gated live switch is enabled.
3. **Trinity degradation** preserves completed trustworthy stages and marks a
   failed stage unavailable.

The current runtime-failover state is reported by
[`/health`](https://verifimind.ysenseai.org/health). Never describe a configured
fallback chain as active runtime failover when that switch is false.

A BYOK error must not be interpreted as successful real inference. Check the
returned stage quality, provider/model attribution, normalized failure class,
retryable flag, and recovery guidance. An incomplete run remains incomplete
even when other stages succeed.

## Safe validation checklist

Before depending on a BYOK route:

1. Confirm the provider and model are present in the live catalogue.
2. Run a benign, non-sensitive standalone test.
3. Verify returned provider/model and `real` quality.
4. Test one red-line or failure case appropriate to your use.
5. Confirm `save_to_history=false` unless aggregate history is explicitly
   intended.
6. Re-check after a provider retires or renames a model.

---

[← Home](Home) · [Tool reference](MCP-Tools-Reference) · [Installation](Installation)
