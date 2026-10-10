# Contributing

Use Python 3.11 or newer and an editable source checkout. Follow the README to
create a virtual environment. Run `python -m unittest discover -s tests -v` and
`python -m pip check` in that environment before opening a pull request.
Tests use fixture data and mocked AI responses; no OpenAI API key is needed.
The demo integration test needs permission to bind a localhost port.

Keep URL allowlists narrow, distinguish missing evidence from false results,
and preserve exact decimal price comparisons. Include a focused regression
test for behavior fixes. Do not commit credentials, live tunnel URLs, generated
archives, or personal catalog state. Use `.env.example` for new settings.

Semantic smoke tests incur API charges and are optional; document their product
cap and outcome separately from deterministic tests. Changes to the local plugin
package do not automatically publish an update to an existing ChatGPT plugin.
