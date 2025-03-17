import matplotlib.pyplot as plt
import numpy as np

# Data extracted from the image
policies = ["Pick First", "Round Robin", "Least Load"]
latencies = [5.17, 0.56, 1.72]  # in seconds
throughputs = [17.28, 123.85, 41.04]  # in requests per second

x = np.arange(len(policies))  # the label locations

# Plot latency comparison
plt.figure(figsize=(10, 5))
plt.bar(x, latencies, color=['red', 'blue', 'green'], alpha=0.7)
plt.xticks(x, policies)
plt.ylabel("Latency (s)")
plt.title("Comparison of Latency Across Policies")
plt.show()

# Plot throughput comparison
plt.figure(figsize=(10, 5))
plt.bar(x, throughputs, color=['red', 'blue', 'green'], alpha=0.7)
plt.xticks(x, policies)
plt.ylabel("Throughput (req/s)")
plt.title("Comparison of Throughput Across Policies")
plt.show()
