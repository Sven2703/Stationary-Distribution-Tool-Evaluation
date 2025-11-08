import java.util.ArrayList;
import java.util.List;

public class Model {
    int states;
    public int SCCs;
    public int BSCCs;
    public int nonBSCCs;
    public int reachableRecurrentStates;
    String name;
    List<StationaryExperiment> stationaryExperiments = new ArrayList<StationaryExperiment>();
    double[] stationaryDistribution;

    public Model(String name) {
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

    public void setStates(int states, int sccs, int bsccs, int nonbsccs) {
        this.states = states;
        SCCs = sccs;
        BSCCs = bsccs;
        nonBSCCs = nonbsccs;
        setReachableRecurrentStates(this.states - nonBSCCs);
    }

    public void setReachableRecurrentStates(int reachableRecurrentStates) {
        //System.out.print("States: " + states);
        this.reachableRecurrentStates = reachableRecurrentStates;
        for (StationaryExperiment stationaryExperiment : stationaryExperiments) {
            stationaryExperiment.reachableRecurrentStates = this.reachableRecurrentStates;
            stationaryExperiment.states = this.states;
            stationaryExperiment.SCCs = this.SCCs;
            stationaryExperiment.BSCCs = this.BSCCs;
            stationaryExperiment.nonBSCCs = this.nonBSCCs;
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
