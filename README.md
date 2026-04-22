# Vapi Rugs Manpower Engine

## Setup
1. Create these folders beside `app.py`:
   - `input/`
   - `output/`
2. Put your original workbook here:
   - `input/Rugs.xlsx`
3. Run:
   - `streamlit run app.py`

## Working behavior
- If `output/Rugs_working.xlsx` exists, the app loads that.
- Otherwise it loads `input/Rugs.xlsx`.
- **Freeze Changes** saves current state to `output/Rugs_working.xlsx`.
- **Reset from Input** deletes the working file and reloads `input/Rugs.xlsx`.

## Notes
- The app uses one live source of truth for final manpower:
  - `st.session_state.master_df`
- PPC Data is the editable asking-rate source.
- Linked helper tables are recalculated in Python and then pushed into the final Rugs master view.
