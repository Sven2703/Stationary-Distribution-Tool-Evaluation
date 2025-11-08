package internalJava;

import java.io.*;
import java.util.List;
import java.util.Scanner;

public class StationaryExperiment {
    double wallClockTime;
    String configurationID;
    String solverID;
    double maxErrorAbsolute;
    double maxErrorRelative;
    double averageErrorAbsoluteInRecurrentStates;
    double averageErrorRelativeInRecurrentStates;
    double mcTime;
    String precision;
    boolean timeout = false;
    boolean executionError = false;
    String tool;
    Model model;
    String name;
    String exportValueFile;
    String log;
    int states;
    public int reachableRecurrentStates;

    public StationaryExperiment(String logFile, List<Model> models) throws FileNotFoundException {
        Scanner input = new Scanner(new FileInputStream(logFile));
        if(logFile.contains(".json")) {
            while (input.hasNext()) {
                String identifier = input.next();
                if (identifier.equals("\"benchmark-id\":")) {
                    name = removeCharacters(input.next());
                } else if (identifier.equals("\"tool\":")) {
                    tool = removeCharacters(input.next());
                } else if (identifier.equals("\"wallclock-time\":")) {
                    String time = removeCharacters(input.next());
                    wallClockTime = Double.parseDouble(time);
                } else if (identifier.equals("\"precision\":")) {
                    precision = removeCharacters(input.next());
                } else if (identifier.equals("\"timeout\":")) {
                    timeout = removeCharacters(input.next()).equals("true");
                } else if (identifier.equals("\"execution-error\":")) {
                    executionError = removeCharacters(input.next()).equals("true");
                } else if (identifier.equals("\"mc-time\":")) {
                    mcTime = Double.parseDouble(removeCharacters(input.next()));
                } else if (identifier.equals("\"configuration-id\":")) {
                    configurationID = removeCharacters(input.next());
                } else if (identifier.equals("\"solver-id\":")) {
                    solverID = removeCharacters(input.next());
                } else if (identifier.equals("\"export-value-file\":")) {
                    exportValueFile = removeCharacters(input.next());
                } else if (identifier.equals("\"log\":")) {
                    log = removeCharacters(input.next());
                } else if (identifier.equals("\"states\":")) {
                    states = Integer.parseInt(removeCharacters(input.next()));
                }
            }
        } else {
            while (input.hasNext()) {
                String identifier = input.next();
                if (identifier.equals("name:")) {
                    name = input.next();
                } else if (identifier.equals("tool:")) {
                    tool = input.next();
                } else if (identifier.equals("wallclock-time:")) {
                    wallClockTime = Double.parseDouble(input.next());
                } else if (identifier.equals("precision:")) {
                    precision = input.next();
                } else if (identifier.equals("timeout:")) {
                    timeout = input.next().equals("true");
                } else if (identifier.equals("execution-error:")) {
                    executionError = input.next().equals("true");
                } else if (identifier.equals("mc-time:")) {
                    mcTime = Double.parseDouble(input.next());
                } else if (identifier.equals("configuration-id:")) {
                    configurationID = input.next();
                } else if (identifier.equals("solver-id:")) {
                    solverID = input.next();
                } else if (identifier.equals("export-value-file:")) {
                    exportValueFile = input.next();
                } else if (identifier.equals("log:")) {
                    log = input.next();
                } else if (identifier.equals("states:")) {
                    states = Integer.parseInt(input.next());
                } else  if (identifier.equals("reachable-recurrent-states:")) {
                    reachableRecurrentStates = Integer.parseInt(input.next());
                }
            }
        }
        for (Model model1 : models) {
            if (model1.getName().equals(name)) {
                model = model1;
                break;
            }
        }
        if (model == null) {
            model = new Model(states, name);
            models.add(model);
        }
        model.addStationaryExperiment(this);
    }

    public void saveResults(String directory) {
        File dir = new File(directory);
        File file = new File(dir + "/" + getName() + ".txt");
        try {
            Writer writer = new BufferedWriter(new FileWriter(file));
            writer.write("wallclock-time: " + wallClockTime + "\n");
            writer.write("tool: " + tool + "\n");
            writer.write("configuration-id: " + configurationID + "\n");
            writer.write("solver-id: " + solverID + "\n");
            writer.write("export-value-file: " + exportValueFile + "\n");
            writer.write("log: " + log + "\n");
            writer.write("states: " + states + "\n");
            writer.write("max-error-absolute: " + maxErrorAbsolute + "\n");
            writer.write("max-error-relative: " + maxErrorRelative + "\n");
            writer.write("average-error-absolute: " + averageErrorAbsoluteInRecurrentStates + "\n");
            writer.write("average-error-relative: " + averageErrorRelativeInRecurrentStates + "\n");
            writer.write("mc-time: " + mcTime + "\n");
            writer.write("precision: " + precision + "\n");
            writer.write("timeout: " + timeout + "\n");
            writer.write("execution-error: " + executionError + "\n");
            writer.write("name: " + name + "\n");
            writer.write("reachable-recurrent-states: " + reachableRecurrentStates + "\n");
            writer.close();
        } catch (IOException e) {
            System.out.println("Error saving results to " + file.getAbsolutePath());
        }
    }

    public String removeCharacters(String input) {
        String output = input.replaceAll("\"", "");
        output = output.replaceAll(",", "");
        return output;
    }

    public void setErrors(double maxErrorAbsolute, double maxErrorRelative, double averageErrorAbsoluteInRecurrentStates, double averageRelativeErrorInRecurrentStates) {
        this.maxErrorAbsolute = maxErrorAbsolute;
        this.maxErrorRelative = maxErrorRelative;
        this.averageErrorAbsoluteInRecurrentStates = averageErrorAbsoluteInRecurrentStates;
        this.averageErrorRelativeInRecurrentStates = averageRelativeErrorInRecurrentStates;
    }

    public String getName() {
        return tool + "." + configurationID + "." + solverID + "." + precision + "." + name;
    }

    public String getPrecision() {
        return precision;
    }

    public Model getModel() {
        return model;
    }

    public String getExportValueFile() {
        return exportValueFile;
    }

    public void printAll() {
        System.out.println("wallclock time: " + wallClockTime);
        System.out.println("precision: " + precision);
        System.out.println("max error absolute: " + maxErrorAbsolute);
        System.out.println("max error relative: " + maxErrorRelative);
        System.out.println("average error absolute: " + averageErrorAbsoluteInRecurrentStates);
        System.out.println("average error relative: " + averageErrorRelativeInRecurrentStates);
        System.out.println("average error absolute: " + averageErrorAbsoluteInRecurrentStates);
        System.out.println("average error relative: " + averageErrorRelativeInRecurrentStates);
        System.out.println("states: " + states);
        System.out.println("tool: " + tool);
        System.out.println("name: " + name);
        System.out.println("export-value-file: " + exportValueFile);
        System.out.println("log: " + log);
        System.out.println("mc-time: " + mcTime);
        System.out.println("timeout " + timeout);
        System.out.println("execution error " + executionError);
    }
}
