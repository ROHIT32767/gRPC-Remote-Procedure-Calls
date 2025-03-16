# MapReduce System - README

## Requirements
To run the MapReduce system, ensure you have the following installed:
- Python 3.7+
- gRPC and gRPC tools (`grpcio`, `grpcio-tools`)
- Required Python libraries:
  ```bash
  pip install grpcio grpcio-tools
  ```

---

## Commands Explanation and Usage

### Running the Master
The Master node coordinates the MapReduce process by splitting the input data, assigning tasks to mappers, and aggregating reducer outputs.

To run the `master.py` script:
```bash
cd P2; cd client; python3 master.py --query <query_number> --mappers <num_mappers> --reducers <num_reducers>
```
- `<query_number>`:
  - `1` for Word Count
  - `2` for Inverted Index
- `<num_mappers>`: Number of mapper processes to spawn
- `<num_reducers>`: Number of reducer processes to spawn

#### Example Usage:
- Word Count with 3 mappers and 2 reducers:
  ```bash
  cd P2; cd client; python3 master.py --query 1 --mappers 3 --reducers 2
  ```
- Inverted Index with 3 mappers and 2 reducers:
  ```bash
  cd P2; cd client; python3 master.py --query 2 --mappers 3 --reducers 2
  ```

---

## Input/Output Format

### Input Data
- The input files are placed in the `dataset/` directory.
- Each file in `dataset/` is processed independently by the mappers.

### Intermediate Data (Mapper Output)
- Intermediate files are stored in the `folders/` directory.
- If there are `M` mappers and `R` reducers, `M * R` intermediate files will be generated.
- These files serve as partitions that reducers will process.

### Final Output
- The final output is stored in the `outputs/` directory as `final_output.txt`.
- The format of `final_output.txt` depends on the query executed:
  - **Word Count (Query 1):**
    ```
    word1 count1
    word2 count2
    ...
    ```
  - **Inverted Index (Query 2):**
    ```
    word1: file1, file2, file3...
    word2: file1, file2...
    ...
    ```

### Reducer Output
- If `R` reducers are used, `R` output files will be stored in `outputs/` before aggregation.
- These files contain partial results, which are combined into `final_output.txt`.

---

## Summary
This MapReduce system efficiently processes large datasets using distributed computing. The Master node coordinates execution, while Mappers and Reducers handle the data transformation. The system supports Word Count and Inverted Index queries, with well-structured intermediate and final outputs.

