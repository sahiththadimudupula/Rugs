# Vapi Rugs Manpower Engine - Build 1

This build includes:
- PPC data editing
- PPC -> Capacity propagation
- PPC -> Coating helper propagation
- PPC -> CS propagation
- PPC -> Hydro propagation
- linked master row refresh for Coating, Cut & Sew, and Hydro row in Dyeing
- fast row-level `Machine_Count -> Formulas -> BE_Scientific_Manpower` recalculation
- Final Master Sheet live reflection

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Load behavior:
- loads `output/Rugs_working.xlsx` if it exists
- otherwise loads `input/Rugs.xlsx`

Freeze Changes:
- writes implemented sheets back to `output/Rugs_working.xlsx`

Reset from Input:
- deletes the working file and rebuilds app state from `input/Rugs.xlsx`

Not included in Build 1:
- EZM/Paddle Dyeing algorithm
- Jet Dyeing algorithm
- Packin&TQM engine
