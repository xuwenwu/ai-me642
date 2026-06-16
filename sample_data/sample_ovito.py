from ovito.io import export_file, import_file
from ovito.modifiers import CoordinationAnalysisModifier


pipeline = import_file("trajectory.dump")
pipeline.modifiers.append(CoordinationAnalysisModifier(cutoff=3.5, number_of_bins=100))
data = pipeline.compute()
export_file(data, "rdf.csv", "txt/table", key="coordination-rdf")
