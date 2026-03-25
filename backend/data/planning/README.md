Nigeria planning CSVs for CareMesh.

Files generated here:
- `lga_profiles_nigeria_worldpop_v2.csv`
- `hospital_capacities_nigeria_grid3_baseline.csv`

Generation:
```powershell
python prepare_nigeria_planning_csvs.py
```

Import into the app:
```powershell
python import_planning_data.py --lga-profiles data\planning\lga_profiles_nigeria_worldpop_v2.csv --hospital-capacities data\planning\hospital_capacities_nigeria_grid3_baseline.csv
```

Notes:
- `lga_profiles_nigeria_worldpop_v2.csv` uses WorldPop Nigeria v2.0 admin level 2 population means.
- The same LGA file now includes centroid coordinates plus nearest-care route distance and travel time generated through the OSRM public routing API.
- `hospital_capacities_nigeria_grid3_baseline.csv` uses real GRID3/NHFR 2024 facility identities and levels, then applies a transparent capacity baseline proxy by facility level because an openly downloadable nationwide facility-by-facility bed and staffing dataset was not available in this workspace.
