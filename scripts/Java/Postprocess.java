import internalJava.Model;
import internalJava.StationaryExperiment;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.util.LinkedList;
import java.util.List;
import java.util.Scanner;

public class Postprocess {
    public static String directory;

    public static void main(String[] args) throws FileNotFoundException {
        String resultDirectory; // = args[0];
        directory = "C:/Schule/Bachelorarbeit/Storm HPC/HPC/run/9.5-stationary-eval";
        String logDirectory = directory + "/results/logs";
        String saveDirectory = directory + "/results/postprocess";

        List<StationaryExperiment> stationaryExperiments = new LinkedList<>();
        List<Model> models = new LinkedList<>();

        File logs = new File(logDirectory);
        //File logs = new File(saveDirectory);

        String[] logList = logs.list();
        for (String log : logList) {
            if(log.contains(".json")) {
                StationaryExperiment stationaryExperiment = new StationaryExperiment(logDirectory + "/" + log, models);
                stationaryExperiments.add(stationaryExperiment);
                if(stationaryExperiment.getPrecision().equals("ignored") && stationaryExperiment.getExportValueFile() != null) {
                    String exportFileName = directory + "/" + stationaryExperiment.getExportValueFile();
                    System.out.println(exportFileName);
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
                    System.out.println(exportFileName);
                    Model model = stationaryExperiment.getModel();
                }
            }
        }

        for (Model model : models) {
            String compare = null;
            for(int i = 0; i < model.getStationaryExperiments().size(); i++) {
                if(model.getStationaryExperiments().get(i).getExportValueFile() != null) {
                    compare = directory + "/" + model.getStationaryExperiments().get(i).getExportValueFile();
                }
            }
            for (StationaryExperiment stationaryExperiment : model.getStationaryExperiments()) {
                if(stationaryExperiment.getExportValueFile() != null) {
                    confirmSimilarity(compare, directory + "/" + stationaryExperiment.getExportValueFile());
                }
            }
        }

        //evaluate(models);

        for (StationaryExperiment stationaryExperiment : stationaryExperiments) {
            //stationaryExperiment.printName();
            //stationaryExperiment.saveResults(saveDirectory);
        }
        for (Model model : models) {
            System.out.println(model.getName());
            System.out.println(model.getReachableRecurrentStates());
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
            double[] correctStationaryDistribution = null;
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
            if(correctFileName != null) {
                //model.setReachableRecurrentStates(correctStationaryDistribution);
                for(StationaryExperiment stationaryExperiment : stationaryExperiments) {
                    if(stationaryExperiment.getExportValueFile() != null && !stationaryExperiment.getPrecision().equals("ignored")) {
                        System.out.println(stationaryExperiment.getExportValueFile());
                        int reachableRecurrentStates = 0;
                        double maxRelativeError = 0;
                        double maxAbsoluteError = 0;
                        double averageRelativeError = 0;
                        double averageAbsoluteError = 0;
                        Scanner correctScanner = new Scanner(new FileInputStream(correctFileName));
                        Scanner scanner =  new Scanner(new FileInputStream(directory + "/" + stationaryExperiment.getExportValueFile()));
                        double real = 0;
                        while(real <= 1.5) {
                            real = buildStationaryStorm(correctScanner);
                            if(real > 1.5) {
                                break;
                            }
                            double approximate = buildStationaryStorm(scanner);
                            if(real > 0.0) {
                                reachableRecurrentStates++;
                                double absoluteError = Math.abs(real - approximate);
                                double relativeError = absoluteError / real;
                                averageAbsoluteError += absoluteError;
                                averageRelativeError += relativeError;
                                if(absoluteError > maxAbsoluteError) {
                                    maxAbsoluteError = absoluteError;
                                }
                                if(relativeError > maxRelativeError) {
                                    maxRelativeError = relativeError;
                                }
                            }
                        }
                        model.setReachableRecurrentStates(reachableRecurrentStates);
                        averageAbsoluteError = averageAbsoluteError / model.getReachableRecurrentStates();
                        averageRelativeError = averageRelativeError / model.getReachableRecurrentStates();
                        stationaryExperiment.setErrors(maxAbsoluteError, maxRelativeError, averageAbsoluteError, averageRelativeError);
                    }
                    //stationaryExperiment.saveResults(directory + "/results/postprocess");
                    //System.out.println("Saved " + stationaryExperiment.getName());
                }
            }
            for (StationaryExperiment stationaryExperiment : model.getStationaryExperiments()) {
                stationaryExperiment.saveResults(directory + "/results/postprocess");
            }
            System.out.println("Saved " + model.getName() + " with " + model.getStates() + " states and in BSCCs " + model.getReachableRecurrentStates());
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
