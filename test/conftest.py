import matplotlib

# Set a headless backend for tests, to stop plt.show() from blocking in headless CI
matplotlib.use("Agg")