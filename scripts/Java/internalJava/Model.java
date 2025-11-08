package internalJava;

import java.util.ArrayList;
import java.util.List;

public class Model {
    int states;
    int reachableRecurrentStates;
    String name;
    List<StationaryExperiment> stationaryExperiments = new ArrayList<StationaryExperiment>();
    double[] stationaryDistribution;

    public Model(int states, String name) {
        this.states = states;
        this.name = name;
    }

    public void addStationaryExperiment(StationaryExperiment stationaryExperiment) {
        stationaryExperiments.add(stationaryExperiment);
    }

    public void computeCorrectness() {

    }

    public List<StationaryExperiment> getStationaryExperiments() {
        return stationaryExperiments;
    }

    public void setStationaryDistribution(double[] stationaryDistribution) {
        this.stationaryDistribution = stationaryDistribution;
        System.out.println(stationaryDistribution.length);
        for (double s : stationaryDistribution) {
            if(s > 0.0) {
                reachableRecurrentStates++;
            }
        }
    }

    public void setReachableRecurrentStates(int stationaryDistribution) {
        //System.out.print("States: " + states);
        reachableRecurrentStates = stationaryDistribution;
        for (StationaryExperiment stationaryExperiment : stationaryExperiments) {
            stationaryExperiment.reachableRecurrentStates = reachableRecurrentStates;
        }
        //System.out.println(", Reachable Recurrent: " + reachableRecurrentStates);
    }

    public String getName() {
        return name;
    }

    public int getStates() {
        return states;
    }

    public int getReachableRecurrentStates() {
        return reachableRecurrentStates;
    }
}
