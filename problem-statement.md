# Mass Transit Billing Challenge

Version: 1.3

## Requirements

- Please complete the following programming exercise. Allow for about 4-6 hours.
- You must use either Python or Go to complete this exercise. You may use the standard library for
  your language freely, but not other third-party libraries. In your test code you may use common
  third-party test packages (e.g. pytest or testify).
- Please produce production-quality code, providing tests and comments where necessary.
- Provide all source code, ideally in a zip file / tarball so that it can be checked out and built.
- Please do not share or upload the code anywhere else (e.g. Github).
- Ensure your solution takes command line arguments described below.
- Provide a brief README file with instructions on how to build/run your program (and tests if
  present) - and any assumptions made.
- Please remove any identifying information from your submission, e.g. don't include your name
  anywhere in your code or README.

## Use of AI

- We use AI tooling internally in a number of areas, but as enhancement rather than replacement of
  engineering skill, so we require all our engineers to be excellent programmers.
- With this challenge, we’re looking to understand your personal problem-solving approach and
  coding style, so please refrain from using AI code-assistance tools (like GitHub Copilot or
  ChatGPT). It's not about perfection, just your approach!

## Exercise

The task is to build a billing system for a mass transit system. The transit system has a network of
train stations, each belonging to a pricing zone. Each time a user enters (IN) or exits (OUT) a
station it is recorded. The data you are provided with is the user_id, direction (either IN or OUT
of the station), the station and the time of the entry/exit (in UTC) for all the journeys in a given
time period. A user can only do one journey at a time. You can assume the data is sorted by
timestamp, but not necessarily by users. You are tasked with calculating the total charge for each
customer at the end of the period.

Each journey has a £2 base fee, and additional costs based on the entry and exit zones.

| Zone | In / Out additional Cost |
| ---- | ------------------------ |
| 1    | £0.80                    |
| 2-3  | £0.50                    |
| 4-5  | £0.30                    |
| 6+   | £0.10                    |

Examples: The price of a journey from zone 1 to zone 1 is 2.00 + 0.80 + 0.80 = £3.60. The price of a
journey from zone 6 to zone 4 is 2.00 + 0.10 + 0.30 = £2.40.

For any erroneous journeys where an IN or OUT is missing, a £5 fee is used as the total journey
price. It should be assumed that all valid journeys are completed before midnight (i.e. all valid
journeys will have an IN and an OUT on the same day).

There is also a daily cap of £15, and a monthly cap of £100. Caps include all journey costs and
fees, and once a given cap is reached the customer pays no extra for the given day or month.

Expected cmd to run:

```bash
<your_program> <zones_file_path> <journey_data_path> <output_file_path>
```

Expected Output: each user_id and their billing_amount (to 2 decimal places) written to
<output_file_path> in user_id alphanumeric increasing order(e.g. ['23Charlie', 'alpha', 'bravo']) as
shown in the example output file.

E.g. to run a Python solution

```bash
python my_solution.py zone_map.csv journey_data.csv output.csv
```

or for a Go solution:

```bash
go run main.go zone_map.csv journey_data.csv output.csv
```
