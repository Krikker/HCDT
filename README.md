# HCDT Shift Assistant for UAZ

`HCDT Shift Assistant` is a demo implementation of a human-centric digital twin for UAZ assembly-line workers.
The system is designed for stations with a high share of manual work: final assembly, quality control, and rework.

## Why this software fits the thesis

The application maps directly to the HCDT architecture from the thesis:

- `Sense`: builds a digital trace of the operator and workstation events.
- `Reason`: evaluates cognitive risk and validates the execution path through a regulation automaton.
- `Act`: generates proactive explainable recommendations instead of simple error messages.
- `Learn`: updates trust score, growth hints, and the bonus coefficient linked to performance.

## Product idea for UAZ

The system acts as a shift assistant for a worker on the UAZ plant floor:

- shows the current operation, equipment context, and next allowed step;
- checks whether the right production tool is selected for the exact station;
- estimates fatigue and cognitive risk before a defect happens;
- explains why a deviation is dangerous and how to correct it on the spot;
- switches the worker into guided learning mode instead of simply blocking the shift;
- calculates trust score, bonus coefficient, and projected shift earnings dynamically.

## Modeled production objects

The software now follows the modeled objects from the thesis more closely:

- welding section;
- assembly section;
- paint section;
- final quality control;
- logistics subsystem;
- plant infrastructure as an extendable integration target.

## Suggested demo scenario

Example station: door assembly and final quality control.

- Operator enters the shift.
- MES assigns a task card.
- SCADA/IIoT sends workstation context.
- The HCDT core builds the operator's live profile.
- If the sequence or tool is suspicious, the system warns before the defect.
- After each cycle, the reputation and motivation metrics are recalculated.

## Project structure

```text
hcdt_vkr/
├── README.md
├── requirements.txt
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── data/
│   │   ├── operators.json
│   │   └── stations.json
│   ├── integrations/
│   │   ├── erp_adapter.py
│   │   ├── mes_adapter.py
│   │   └── scada_adapter.py
│   ├── services/
│   │   ├── digital_trace.py
│   │   ├── recommendation_engine.py
│   │   ├── regulation_engine.py
│   │   ├── reputation_engine.py
│   │   ├── risk_engine.py
│   │   └── twin_service.py
│   └── static/
│       ├── app.js
│       ├── index.html
│       └── style.css
└── tests/
    └── test_hcdt.py
```

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## HCDT requirements covered

- Operator + equipment as a single control object.
- Real-time digital trace.
- Cognitive risk index.
- Executable regulation automaton.
- Explainable support before the mistake.
- Trust score and bonus coefficient.
- Integration stubs for `MES`, `ERP`, `SCADA`, `OPC UA`, and `MQTT`.

## Thesis-ready positioning

This software can be described in the VKR as:

`A decision-support platform for assembly-line workers at UAZ based on the HCDT architecture, focused on proactive defect prevention on manual stations.`
