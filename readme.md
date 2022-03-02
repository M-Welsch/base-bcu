# Backup Server (BaSe): Backup Control Unit (BCU)

The BCU runs on the SBC (bananapi M1) and controls the whole backup process in a very fault-tolerant way.

After power-up it basically does the following

- setup schedule and wait for the point of time when the backup shall be made. Or make the backup immediately if the user requested it.
- connect to the data source (via network) and data sink (mechanically)
- invoke rsync to create an incremental backup
- disconnect from data source and sink
- set wakeup timer on SBU
- power down

## Tests

run `pytest test` from the base-bcu directory.

### Classification:

- `unit` hardware independent unit tests
- `integration` hardware independent tests for features
- `system` hardware independent tests for the whole flow-chard
- `hardware_dependent` tests on the actual hardware (does only work on compatible SBCs which is only tha bananapi M1 for now). These tests can be used as end-of-line tests
