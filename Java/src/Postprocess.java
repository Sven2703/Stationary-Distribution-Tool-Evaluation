import java.io.*;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.Scanner;

public class Postprocess {
    public static String directory;
    static boolean evaluateRawData = false;

    public static void main(String[] args) throws FileNotFoundException {
        String resultDirectory; // = args[0];
        directory = "C:/Schule/Bachelorarbeit/Storm HPC/HPC/run/9.5-stationary-eval";
        String logDirectory = directory + "/results/logs";
        String saveDirectory = directory + "/results/postprocess";

        List<StationaryExperiment> stationaryExperiments = new LinkedList<>();
        List<Model> models = new LinkedList<>();

        File logs;
        if(evaluateRawData){
            logs = new File(logDirectory);
        } else {
            logs = new File(saveDirectory);
        }

        String[] logList = logs.list();
        for (String log : logList) {
            if(log.contains(".json")) {
                StationaryExperiment stationaryExperiment = new StationaryExperiment(logDirectory + "/" + log, models);
                stationaryExperiments.add(stationaryExperiment);
                if(stationaryExperiment.getPrecision().equals("ignored") && stationaryExperiment.getExportValueFile() != null) {
                    String exportFileName = directory + "/" + stationaryExperiment.getExportValueFile();
                    //System.out.println(exportFileName);
                    Model model = stationaryExperiment.getModel();
                    if(model.getReachableRecurrentStates() == 0) {
                        //model.setStationaryDistribution(buildStationaryArrayStorm(new Scanner(new FileInputStream(exportFileName))));
                    }
                }
            } else if(log.contains(".txt")) {
                StationaryExperiment stationaryExperiment = new StationaryExperiment(saveDirectory + "/" + log, models);
                stationaryExperiments.add(stationaryExperiment);
                if(stationaryExperiment.getPrecision().equals("ignored") && stationaryExperiment.getExportValueFile() != null) {
                    String exportFileName = directory + "/" + stationaryExperiment.getExportValueFile();
                    //System.out.println(exportFileName);
                    Model model = stationaryExperiment.getModel();
                }
            } else if(log.contains(".log")) {
                if(log.contains("hybrid-rel") || log.contains("sparse-rel")) {
                    String modelName = log.replace(".log", "");
                    modelName = modelName.replace("prism.sparse-rel.default.0.001.", "");
                    modelName = modelName.replace("prism.hybrid-rel.default.0.001.", "");
                    Model model = null;
                    for(Model model1 : models) {
                        if(model1.getName().equals(modelName)) {
                            model = model1;
                            break;
                        }
                    }
                    if(model != null) {
                        //System.out.println(model.name + " adding state numbers through " + log);
                        Scanner inputLog = new Scanner(new FileInputStream(logDirectory + "/" + log));
                        int sccs = 0;
                        int bsccs = 0;
                        int nonbsccs = 0;
                        int states = 0;
                        while (inputLog.hasNext()) {
                            String next = inputLog.next();
                            if(next.equals("States:")) {
                                states = Integer.parseInt(inputLog.next());
                            }
                            if(next.equals("SCCs:")) {
                                try {
                                    String sccString = inputLog.next();
                                    sccs = Integer.parseInt(sccString.replace(",", ""));
                                    inputLog.next();
                                    sccString = inputLog.next();
                                    bsccs = Integer.parseInt(sccString.replace(",", ""));
                                    inputLog.next();
                                    inputLog.next();
                                    sccString = inputLog.next();
                                    nonbsccs = Integer.parseInt(sccString);
                                    break;
                                } catch (Exception e) {
                                    System.out.println("Error while reading log file " + log);
                                }
                            }
                            if(sccs == 0 && bsccs == 0 && nonbsccs == 0 && states == 0) {
                                if(model.getName().equals("crafted-loop.1000000")) {
                                    states = 1000000;
                                    sccs = 1;
                                    bsccs = 1;
                                } else if(model.getName().equals("lumbroso.64000")) {
                                    states = 3264511;
                                    bsccs = 64000;
                                    nonbsccs = states - 64000;
                                } else if(model.getName().equals("lumbroso.4000")) {
                                    states = 204031;
                                    bsccs = 4000;
                                    nonbsccs = states - 4000;
                                } else if(model.getName().equals("lumbroso.1000")) {
                                    states = 51007;
                                    bsccs = 1000;
                                    nonbsccs = states - 1000;
                                } else if(model.getName().equals("lumbroso.16000")) {
                                    states = 816127;
                                    bsccs = 16000;
                                    nonbsccs = states - 16000;
                                }
                            }
                        }
                        //System.out.println("SCCs: " + sccs + ", BSCCs: " + bsccs + ", nonBSCCs: " + nonbsccs);
                        model.setStates(states, sccs, bsccs, nonbsccs);
                    } else {
                        System.out.println("No " + modelName + " found");
                    }
                }
            }
        }


        /*for (Model model : models) {
            String compare = null;
            for(int i = 0; i < model.getStationaryExperiments().size(); i++) {
                StationaryExperiment stationaryExperiment = model.getStationaryExperiments().get(i);
                if(stationaryExperiment.getExportValueFile() != null && stationaryExperiment.getTool().equals("storm")) {
                    compare = directory + "/" + model.getStationaryExperiments().get(i).getExportValueFile();
                }
            }
            for (StationaryExperiment stationaryExperiment : model.getStationaryExperiments()) {
                if(stationaryExperiment.getExportValueFile() != null && stationaryExperiment.getTool().equals("storm")) {
                    confirmSimilarity(compare, directory + "/" + stationaryExperiment.getExportValueFile());
                }
            }
            System.out.println("Checked model: " + model.getName());
        }*/

        if(evaluateRawData)
            evaluate(models);

        buildCSVForAll(stationaryExperiments, models, saveDirectory, "all");
        List<Model> oneStationary = new LinkedList<>();
        List<Model> allStationary = new LinkedList<>();
        List<Model> onlySingleStationary = new LinkedList<>();
        List<Model> onlyMixed = new LinkedList<>();
        for(Model model : models) {
            if(model.reachableRecurrentStates == 1) {
                oneStationary.add(model);
            } else if(model.reachableRecurrentStates == model.BSCCs) {
                onlySingleStationary.add(model);
            } else if(model.reachableRecurrentStates == model.states) {
                allStationary.add(model);
            } else {
                onlyMixed.add(model);
            }
        }
        buildCSVForAll(stationaryExperiments, oneStationary, saveDirectory, "oneStationary");
        buildCSVForAll(stationaryExperiments, allStationary, saveDirectory, "allStationary");
        buildCSVForAll(stationaryExperiments, onlySingleStationary, saveDirectory, "singletonBSCCs");
        buildCSVForAll(stationaryExperiments, onlyMixed, saveDirectory, "mixed");

        for (StationaryExperiment stationaryExperiment : stationaryExperiments) {
            //if(stationaryExperiment.getTool().equals("prism")) {
                //buildRealPrismJson("C:/Schule/Bachelorarbeit/Storm HPC/HPC/run/share/9.5-stationary-eval/results/logs", stationaryExperiment.getName(), logDirectory + "/" + stationaryExperiment.getName() + ".json");
            //}
        }
        for (Model model : models) {
            //System.out.println(model.getName());
            //System.out.println(model.getReachableRecurrentStates());
        }



        //"C:/Schule/Bachelorarbeit/Storm HPC/HPC/run/9.5-stationary-eval/results/logs/exports/storm.sparse.classic-gmres-topo.0.001.embedded.4.json"
        //"C:/Schule/Bachelorarbeit/Storm HPC/HPC/run/9.5-stationary-eval/results/logs/exports/storm.sparse.classic-gmres-topo.0.001.haddad-monmege.20-0.7.json"
        //C:/Schule/Bachelorarbeit/Storm HPC/HPC/run/9.5-stationary-eval/results/logs/exports/storm.sparse.classic-luexact-topo.ignored.haddad-monmege.20-0.7.json
        //Scanner input = new Scanner(new FileInputStream("C:/Schule/Bachelorarbeit/Storm HPC/HPC/run/9.5-stationary-eval/results/logs/exports/storm.sparse.classic-luexact-topo.ignored.haddad-monmege.20-0.7.json"));
        //double[] stationaryDistribution = buildStationaryArrayStorm(input);
        //for (int i = 1; i < stationaryDistribution.length; i++) {
        //    System.out.println(stationaryDistribution[i] + stationaryDistribution[i - 1]);
        //}
        //for (double v : stationaryDistribution) {
        //System.out.print(v + ", ");
        //}
        //StationaryExperiment test = new StationaryExperiment(resultDirectory + "/logs/storm.sparse.classic-gmres-topo.0.001.haddad-monmege.20-0.7.json");
        //test.printAll();
    }

    public static void evaluate(List<Model> models) throws FileNotFoundException {
        for (Model model : models) {
            System.out.println(model.getName());
            List<StationaryExperiment> stationaryExperiments = model.getStationaryExperiments();
            String correctFileName = null;
            for (StationaryExperiment stationaryExperiment : stationaryExperiments) {
                if(stationaryExperiment.getPrecision().equals("ignored")) {
                    try {
                        correctFileName = directory + "/" + stationaryExperiment.getExportValueFile();
                        //correctStationaryDistribution = buildStationaryArrayStorm(new Scanner(new FileInputStream(exportFileName)));
                        Scanner test = new Scanner(new FileInputStream(correctFileName));
                        test.close();
                        break;
                    } catch (FileNotFoundException e) {
                        correctFileName = null;
                    }
                }
            }
            //model.setReachableRecurrentStates(correctStationaryDistribution);
            for(StationaryExperiment stationaryExperiment : stationaryExperiments) {
                if (stationaryExperiment.getExportValueFile() != null
                        && !stationaryExperiment.getPrecision().equals("ignored")
                        && stationaryExperiment.getTool().equals("storm")) {
                    //System.out.println(stationaryExperiment.getExportValueFile());
                    double maxRelativeError = 0;
                    double maxAbsoluteError = 0;
                    double averageRelativeError = 0;
                    double averageAbsoluteError = 0;
                    Scanner correctScanner = null;
                    if(correctFileName != null) {
                        correctScanner = new Scanner(new FileInputStream(correctFileName));
                    }
                    Scanner scanner = new Scanner(new FileInputStream(directory + "/" + stationaryExperiment.getExportValueFile()));
                    double approximate = 0;
                    while (approximate <= 1.5) {
                        approximate = buildStationaryStorm(scanner);
                        if (approximate > 1.5) {
                            if(correctFileName != null) {
                                buildStationaryStorm(correctScanner);
                            }
                            break;
                        }
                        double real = approximate;
                        if(correctFileName != null) {
                            real = buildStationaryStorm(correctScanner);
                        }
                        if (real > 0.0) {
                            double absoluteError = Math.abs(real - approximate);
                            double relativeError = absoluteError / real;
                            maxAbsoluteError += approximate;
                            if(correctFileName != null) {
                                averageRelativeError += relativeError;
                            }
                            if (relativeError > maxRelativeError) {
                                maxRelativeError = relativeError;
                            }
                        }
                    }
                    if(correctFileName != null) {
                        if (correctScanner.hasNext()) {
                            System.out.println(correctFileName + " has more lines!");
                        }
                    }
                    if (scanner.hasNext()) {
                        System.out.println(stationaryExperiment.getExportValueFile() + " has more lines as " + correctFileName);
                    }
                    maxAbsoluteError = Math.abs(maxAbsoluteError - 1);
                    averageAbsoluteError = maxAbsoluteError / model.getReachableRecurrentStates();
                    averageRelativeError = averageRelativeError / model.getReachableRecurrentStates();
                    stationaryExperiment.setErrors(maxAbsoluteError, maxRelativeError, averageAbsoluteError, averageRelativeError);
                } else if (stationaryExperiment.getExportValueFile() != null
                        && !stationaryExperiment.getPrecision().equals("ignored")
                        && stationaryExperiment.getTool().equals("prism")) {

                    Scanner scanner = new Scanner(new FileInputStream(directory + "/" + stationaryExperiment.getExportValueFile()));
                    double maxAbsoluteError = 0;
                    double averageAbsoluteError = 0;
                    while (scanner.hasNext()) {
                        double value = Double.parseDouble(scanner.next());
                        maxAbsoluteError += value;
                    }
                    maxAbsoluteError = Math.abs(maxAbsoluteError - 1);
                    averageAbsoluteError = maxAbsoluteError / model.getReachableRecurrentStates();
                    stationaryExperiment.setErrors(maxAbsoluteError, 0, averageAbsoluteError, 0);
                }
                //stationaryExperiment.saveResults(directory + "/results/postprocess");
                //System.out.println("Saved " + stationaryExperiment.getName());
            }
            for(StationaryExperiment stationaryExperiment : stationaryExperiments) {

            }
            for (StationaryExperiment stationaryExperiment : model.getStationaryExperiments()) {
                stationaryExperiment.saveResults(directory + "/results/postprocess");
            }
            System.out.println("Saved " + model.getName() + " with " + model.getStates() + " states and in BSCCs " + model.getReachableRecurrentStates());
        }
    }

    public static void buildCSVForAll(List<StationaryExperiment> stationaryExperiments, List<Model> models, String directory, String name) {
        List<String> toolConfigurations = new LinkedList<>();
        boolean[] stormExactExists = new boolean[models.size()];
        for (StationaryExperiment stationaryExperiment : stationaryExperiments) {
            if(stationaryExperiment.getPrecision().equals("ignored") && stationaryExperiment.getExportValueFile() != null) {
                Model model = stationaryExperiment.getModel();
                for(int i = 0; i < models.size(); i++) {
                    if(model == models.get(i)) {
                        stormExactExists[i] = true;
                        break;
                    }
                }
            }
            String configuration = stationaryExperiment.getToolConfiguration();
            boolean alreadySaved = false;
            for (String toolConfiguration : toolConfigurations) {
                if(toolConfiguration.equals(configuration)) {
                    alreadySaved = true;
                    break;
                }
            }
            if(!alreadySaved) {
                toolConfigurations.add(configuration);
            }
        }
        int x = toolConfigurations.size() + 3;
        int y = models.size() + 1;
        String[][] dataMaxAbsolute = new String[y][x];
        buildFirstRowAndColumn(dataMaxAbsolute, toolConfigurations, models);
        String[][] dataAverageAbsolute = new String[y][x];
        buildFirstRowAndColumn(dataAverageAbsolute, toolConfigurations, models);
        String[][] dataMaxRelative = new String[y][x];
        buildFirstRowAndColumn(dataMaxRelative, toolConfigurations, models);
        String[][] dataAverageRelative = new String[y][x];
        buildFirstRowAndColumn(dataAverageRelative, toolConfigurations, models);
        String[][] dataTime = new String[y][x];
        buildFirstRowAndColumn(dataTime, toolConfigurations, models);
        String[][] dataCorrectTime = new String[y][x];
        buildFirstRowAndColumn(dataCorrectTime, toolConfigurations, models);

        int[] correct = new int[x];
        int[] wrong = new int[x];

        for(StationaryExperiment stationaryExperiment : stationaryExperiments) {
            int x1 = 0;
            int y1 = 0;
            String toolConfiguration = stationaryExperiment.getToolConfiguration();
            Model model = stationaryExperiment.getModel();
            for(int i = 0; i < models.size(); i++) {
                if(model == models.get(i)) {
                    x1 = i + 1;
                    break;
                }
            }
            for(int i = 0; i < toolConfigurations.size(); i++) {
                if(toolConfiguration.equals(toolConfigurations.get(i))) {
                    y1 = i + 3;
                    break;
                }
            }
            if(x1 != 0 && y1 != 0) {
                if(stationaryExperiment.getExportValueFile() != null && !(stationaryExperiment.executionError || stationaryExperiment.timeout)) {
                    if(stationaryExperiment.getTool().equals("storm")) {
                        if(stationaryExperiment.maxErrorAbsolute > 0.000001)
                            System.out.println(stationaryExperiment.getName() + " maxAbsoluteError: " + stationaryExperiment.maxErrorAbsolute);
                        double maxAbsoluteError = computeCSVDouble(stationaryExperiment.maxErrorAbsolute, true);
                        double maxRelativeError = computeCSVDouble(stationaryExperiment.maxErrorRelative, stormExactExists[x1 - 1]);
                        dataMaxAbsolute[x1][y1] = Double.toString(maxAbsoluteError);
                        dataMaxRelative[x1][y1] = Double.toString(maxRelativeError);
                        double averageAbsoluteError = computeCSVDouble(stationaryExperiment.averageErrorAbsoluteInRecurrentStates, true);
                        double averageRelativeError = computeCSVDouble(stationaryExperiment.averageErrorRelativeInRecurrentStates, stormExactExists[x1 - 1]);
                        dataAverageAbsolute[x1][y1] = Double.toString(averageAbsoluteError);
                        dataAverageRelative[x1][y1] = Double.toString(averageRelativeError);
                        if(maxRelativeError < 0.001) {
                            correct[y1]++;
                            double value = stationaryExperiment.wallClockTime;
                            if(value < 1) {
                                value = 1;
                            }
                            dataCorrectTime[x1][y1] = Double.toString(value);
                        } else {
                            dataCorrectTime[x1][y1] = "6000";
                            wrong[y1]++;
                        }
                    } else {
                        double averageAbsoluteError = computeCSVDouble(stationaryExperiment.averageErrorAbsoluteInRecurrentStates, true);
                        dataAverageAbsolute[x1][y1] = Double.toString(averageAbsoluteError);
                        double maxAbsoluteError = computeCSVDouble(stationaryExperiment.maxErrorAbsolute, true);
                        if(maxAbsoluteError < 0.001) {
                            correct[y1]++;
                            double value = stationaryExperiment.wallClockTime;
                            if(value < 1) {
                                value = 1;
                            }
                            dataCorrectTime[x1][y1] = Double.toString(value);
                        } else {
                            dataCorrectTime[x1][y1] = "6000";
                            wrong[y1]++;
                        }
                        dataMaxAbsolute[x1][y1] = Double.toString(maxAbsoluteError);
                        dataMaxRelative[x1][y1] = "-15";
                        dataAverageRelative[x1][y1] = "-15";
                    }
                } else if(!stationaryExperiment.getTool().equals("sds") || stationaryExperiment.executionError || stationaryExperiment.timeout) {
                    dataMaxAbsolute[x1][y1] = "5";
                    dataMaxRelative[x1][y1] = "5";
                    dataAverageAbsolute[x1][y1] = "5";
                    dataAverageRelative[x1][y1] = "5";
                } else {
                    dataMaxAbsolute[x1][y1] = "-15";
                    dataMaxRelative[x1][y1] = "-15";
                    dataAverageAbsolute[x1][y1] = "-15";
                    dataAverageRelative[x1][y1] = "-15";
                }
                if(stationaryExperiment.timeout || stationaryExperiment.executionError) {
                    dataTime[x1][y1] = "6000";
                    dataCorrectTime[x1][y1] = "6000";
                } else if(stationaryExperiment.getExportValueFile() != null || stationaryExperiment.getTool().equals("sds")) {
                    double value = stationaryExperiment.wallClockTime;
                    if(value < 1) {
                        value = 1;
                    }
                    dataTime[x1][y1] = Double.toString(value);
                    if(stationaryExperiment.getTool().equals("sds")) {
                        correct[y1]++;
                        dataCorrectTime[x1][y1] = Double.toString(value);
                    }
                } else {
                    System.out.println(stationaryExperiment.getName() + " has no export file and no errors!");
                }
            }
        }
        for(int i = 0; i < toolConfigurations.size(); i++) {
            System.out.println(name + ": " + toolConfigurations.get(i) + " solved " + correct[i + 3] + " correct of " + models.size());
            System.out.println(name + ": " + toolConfigurations.get(i) + " solved " + wrong[i + 3] + " incorrect");
        }

        buildCSV(directory, name + "-maxAbsolute", dataMaxAbsolute);
        buildCSV(directory, name + "-maxRelative", dataMaxRelative);
        buildCSV(directory, name + "-averageAbsolute", dataAverageAbsolute);
        //buildCSV(directory, name + "-averageRelative", dataAverageRelative);
        buildCSV(directory, name + "-time", dataTime);
        buildCSV(directory, name + "-correctTime", dataCorrectTime);
        if(models.size() == 73) {
            String[][] sortedTime = buildSortedTime(dataCorrectTime);
            buildCSV(directory, name + "-sortedTime", sortedTime);
        }
    }

    public static String[][] buildSortedTime(String[][] data) {
        String[][] sortedTime = new String[data.length][data[0].length - 2];
        for(int j = 3; j < data[0].length; j++) {
            sortedTime[0][j - 2] = data[0][j] + "shifted";
        }
        sortedTime[0][0] = "n";
        for(int i = 1; i < data.length; i++) {
            sortedTime[i][0] = Integer.toString(i);
        }
        for(int i = 1; i < data.length; i++) {
            for(int j = 3; j < data[0].length; j++) {
                double lowest = 6000;
                int index = 0;
                for(int k = 1; k < data.length; k++) {
                    double value = Double.parseDouble(data[k][j]);
                    if(value < lowest) {
                        lowest = value;
                        index = k;
                    }
                }
                if(lowest < 6000) {
                    sortedTime[i][j - 2] = Double.toString(lowest);
                    data[index][j] = "6000";
                } else {
                    sortedTime[i][j - 2] = "";
                }
            }
        }
        return sortedTime;
    }

    public static void buildFirstRowAndColumn(String[][] data, List<String> toolConfigurations, List<Model> models) {
        String[] firstRow = data[0];
        firstRow[0] = "Benchmark-id";
        firstRow[1] = "states";
        firstRow[2] = "stationary-category";
        for(int i = 0; i < toolConfigurations.size(); i++) {
            firstRow[i + 3] = toolConfigurations.get(i);
        }
        for(int i = 1; i <= models.size(); i++) {
            Model model = models.get(i - 1);
            data[i][0] = model.getName();
            data[i][1] = Integer.toString(model.states);
            if(model.reachableRecurrentStates == 1) {
                data[i][2] = "one-singleton-recurrent";
            } else if(model.reachableRecurrentStates == model.BSCCs) {
                data[i][2] = "singleton-recurrent";
            } else if(model.reachableRecurrentStates == model.states) {
                data[i][2] = "fully-recurrent";
            } else {
                data[i][2] = "mixed";
            }
        }
    }

    public static double computeCSVDouble(double value, boolean exactExists) {
        if(exactExists) {
            if(value > 1) {
                value = 1;
            } else if(value < 0.0000001) {
                value = 0.0000001;
            }
        } else {
            value = -15;
        }
        return value;
    }

    public static void buildCSV(String directory, String name, String[][] data) {
        File dir = new File(directory);
        File file = new File(dir + "/" + name + ".csv");
        try {
            Writer writer = new BufferedWriter(new FileWriter(file));
            for (String[] row : data) {
                for (int i = 0; i < row.length; i++) {
                    String cell = row[i];
                    if(cell != null) {
                        writer.write(cell);
                    } else {
                        writer.write("null");
                    }
                    if (i < row.length - 1) {
                        writer.write(";");
                    }
                }
                writer.write("\n");
            }
            writer.close();
        } catch (IOException e) {
            System.out.println("Error while writing CSV file");
        }
    }

    public static double buildStationaryStorm(Scanner scanner) {
        while(scanner.hasNext()) {
            if(scanner.next().equals("\"v\":")) {
                String number = scanner.next();
                try {
                    return Double.parseDouble(number);
                } catch (NumberFormatException e) {
                    return 0;
                }
            }
        }
        return 2;
    }

    public static void buildRealPrismJson(String directory, String experimentName, String oldFile) throws FileNotFoundException {
        Scanner scanner = new Scanner(new FileInputStream(oldFile));
        File dir = new File(directory);
        File file = new File(dir + "/" + experimentName + ".json");
        try {
            Writer writer = new BufferedWriter(new FileWriter(file));
            while (scanner.hasNext()) {
                String line = scanner.nextLine();
                if(line.contains("\"execution-error\":")) {
                    String nextLine = scanner.nextLine();
                    if(nextLine.contains("return-codes")) {
                        String nextNextLine = scanner.nextLine();
                        String close = scanner.nextLine();
                        String notes = scanner.nextLine();
                        String toolResult = scanner.nextLine();
                        String error = scanner.nextLine();
                        if(nextNextLine.contains("0") && !error.contains("Export file ")) {
                            String newLine = line.replace("true", "false");
                            writer.write(newLine + "\n");
                            writer.write(nextLine + "\n");
                            writer.write(nextNextLine + "\n");
                            System.out.println(nextNextLine);
                        } else {
                            System.out.println(nextNextLine + " does not contain 0 in file " + oldFile);
                            writer.write(line + "\n");
                            writer.write(nextLine + "\n");
                            writer.write(nextNextLine + "\n");
                        }
                        writer.write(close + "\n");
                        writer.write(notes + "\n");
                        writer.write(toolResult + "\n");
                        writer.write(error + "\n");
                    } else {
                        System.out.println(nextLine + " does not contain return-codes in " + oldFile);
                    }
                } else {
                    writer.write(line + "\n");
                }
            }
            writer.close();
        } catch (IOException e) {
            System.out.println("Error saving results to " + file.getAbsolutePath());
        }
    }

    public static void buildRealJson(String directory, String experimentName, String oldFile) throws FileNotFoundException {
        Scanner scanner = new Scanner(new FileInputStream(oldFile));
        File dir = new File(directory);
        File file = new File(dir + "/" + experimentName + ".json");
        try {
            Writer writer = new BufferedWriter(new FileWriter(file));
            int state = 0;
            while (scanner.hasNext()) {
                String line = scanner.nextLine();
                if(line.contains("\"s\":")) {
                    String newLine = line.replace("{", state + ",");
                    writer.write(newLine + "\n");
                    state++;
                    while (scanner.hasNext()) {
                        if(scanner.nextLine().contains("},"))
                            break;
                    }
                } else {
                    writer.write(line + "\n");
                }
            }
            writer.close();
        } catch (IOException e) {
            System.out.println("Error saving results to " + file.getAbsolutePath());
        }
    }

    public static void confirmSimilarity(String file1, String file2) throws FileNotFoundException {
        Scanner scanner1 = new Scanner(new FileInputStream(file1));
        Scanner scanner2 = new Scanner(new FileInputStream(file2));
        while(scanner1.hasNext() && scanner2.hasNext()) {
            String next1 = scanner1.next();
            String next2 = scanner2.next();
            if(next1.equals("\"v\":") && next2.equals("\"v\":")) {
                scanner1.next();
                scanner2.next();
            } else if (!next1.equals(next2)){
                System.out.println("Similarity Error between File " +  file1 + " and " + file2);
                System.out.println(next1 + " and " + next2 + " are not equal");
                System.out.println();
                break;
            }
        }
    }

    public static double[] buildStationaryArrayStorm(Scanner scanner) {
        LinkedList<String> list = new LinkedList<>();
        while(scanner.hasNext()) {
            if(scanner.next().equals("\"v\":")) {
                list.add(scanner.next());
            }
        }
        double[] array = new double[list.size()];
        for(int i = 0; i < array.length; i++) {
            String number = list.get(i);
            array[i] = Double.parseDouble(number);
        }
        return array;
    }
}
