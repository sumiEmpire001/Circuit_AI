# CircuitLM 0.2

Run `python training/train.py` to fit the committed model from scratch. The 286 authored descriptions in `corpus_v1.json` cover eight circuit intents and an unsupported class. The model is multinomial naive Bayes with equal class priors and additive smoothing of 0.1. It uses no external inference API or pretrained weights.

The Studio's local parser classifies prompts and checks them against reviewed requests before returning deterministic reference netlists. The temperature motor, Mega light sensor, Mega light sensor with a separately powered servo, and Schmitt inverter are newly available in local mode. Other circuit specifications can use explicit component/net input. Unknown prose constraints cause a clarification response.

`evaluation.json` preserves eight historical authored classification cases. The frontend benchmark also exercises reviewed aliases and a request with an additional unsupported constraint. These checks measure classification and the API's acceptance boundary on authored examples. See [TESTING.md](../TESTING.md) for separate routing results and coverage limits.
