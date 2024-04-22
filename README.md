An Empirical Study on Exception Handling Practices in Python Open-Source Projects
---
This repository includes the source code and data for our paper "An Empirical Study on Exception Handling Practices in Python Open-Source Projects".

## Requirements

- Python 3.6+

## Virtualenv (Windows)
1. Run `py -3.10 -m venv {virtualenv name}`
2. Go to Scripts repository in `{virtualenv name}/Scripts`
3. Run `activate`
4. 

## Build
To reproduce the results, follow the instructions below.

1. Back to root directory
2. Run `pip install -r requirements.txt` 

## Usage

1. Run the script with the command `python miner.py -in <input_path> -o <output_dir> -lang <language>`

### Parameters

- `<input_path>`: Path to the CSV file that contains the name, repo, and source. This is a required parameter.
- `<output_dir>`: Path to the output directory. If not provided, the default is `output`.
- `<language>`: Programming language of the input file(s). Available options are python, typescript. If not provided, the default is `python`.

### Example

To run the script on a CSV file named `input.csv`, output the results to a directory named `results`, and specify the language as `python`, you would use the following command:

```bash
python miner.py -in input.csv -o results -lang python
```
## Unit tests
To run the unit tests, follow the instructions below.

1. Run `python3 -m unittest`

## Coverage report  
To generate the coverage report, follow the instructions below.

1. Run `coverage run -m unittest`
2. Run `coverage report --omit *test_*,*__init__*`
