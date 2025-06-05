# Python Code Execution API

A secure API service that executes arbitrary Python code using Flask and nsjail.

## API Endpoints

- `GET /` - Health check endpoint
- `POST /execute` - Execute Python code

## Usage

### Execute Code

Send a POST request to `/execute` with a JSON body containing the Python script:

```json
{
  "script": "def main():\n    return {'message': 'Hello world!'}"
}
```

Requirements:
- The script must contain a `main()` function
- The `main()` function must return a JSON-serializable object

Response format:
```json
{
  "result": {}, // Return value from main()
  "stdout": "" // Output from print statements
}
```

## Examples

### Pandas Example

```bash
curl -X POST https://nsjail-stacksync-1001605364148.us-east4.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import pandas as pd\n\ndef main():\n    df = pd.DataFrame({\"A\": [1, 2, 3], \"B\": [4, 5, 6]})\n    print(\"Created DataFrame\")\n    return df.to_dict(\"records\")"
  }'
```

### NumPy Example

```bash
curl -X POST https://nsjail-stacksync-1001605364148.us-east4.run.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "import numpy as np\n\ndef perform_matrix_operations():\n    # Create sample matrices\n    matrix_a = np.array([[4, 2, 1], [7, 5, 3], [1, 3, 8]])  # Non-singular matrix\n    matrix_b = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])\n    \n    # Perform operations\n    determinant = np.linalg.det(matrix_a)\n    inverse = np.linalg.inv(matrix_a)\n    dot_product = np.dot(matrix_a, matrix_b)\n    eigenvalues, eigenvectors = np.linalg.eig(matrix_a)\n    \n    # Calculate statistics on combined data\n    all_values = np.concatenate([matrix_a.flatten(), matrix_b.flatten()])\n    stats = {\n        \"mean\": float(np.mean(all_values)),\n        \"median\": float(np.median(all_values)),\n        \"std_dev\": float(np.std(all_values)),\n        \"min\": float(np.min(all_values)),\n        \"max\": float(np.max(all_values))\n    }\n    \n    return {\n        \"determinant\": float(determinant),\n        \"dot_product\": dot_product.tolist(),\n        \"eigenvalues\": eigenvalues.real.tolist(),\n        \"statistics\": stats\n    }\n\ndef main():\n    print(\"Performing matrix operations with NumPy...\")\n    result = perform_matrix_operations()\n    print(\"Completed calculations with determinant: \" + str(result[\"determinant\"]))\n    return result"
  }'
```

## Running Locally

```bash
# Build the Docker image
docker build -t python-execution-api .

# Run the container
docker run -p 8080:8080 python-execution-api
```

Then test locally:
```bash
curl -X POST http://localhost:8080/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"message\": \"Hello from local container\"}"
  }'
```