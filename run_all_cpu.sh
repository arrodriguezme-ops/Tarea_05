set -e
python -m scripts.transcribe_all --task interview --models small base --compute int8 --devices cpu
python -m scripts.transcribe_all --task interview --models small --compute float32 --devices cpu
python -m scripts.transcribe_all --task interview --models small --compute int8 --devices cpu --glossary
python -m scripts.transcribe_all --task order --levels L0 L1 L2 L3 --models small --compute int8 --devices cpu
python -m scripts.transcribe_all --task order --models base --compute int8 --devices cpu
