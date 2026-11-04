# MatchWay (Campus Ride Match & Share System)

Students request an on-demand shared ride (cab/auto/bike) and are instantly
grouped with compatible peers. Two flows: Campus to Destination, and
Pickup to Campus using nearby "virtual spots".

## Tech stack (strict, do not change or add anything else)
- Frontend: React Native, Android Studio, Axios
- Backend: Python, FastAPI
- Database: Supabase
- Auth and storage: Supabase Auth + Storage
- Maps: Ola Maps API
- Verification: PyTesseract (OCR), DeepFace (face recognition)

Rules:
- Do not add any other framework, database or library without asking me first.
- Write every data structure by hand as our own class in plain Python:
  HashMap, Queue, MinHeap, KDTree, IntervalTree, Trie, BipartiteGraph.
- Do NOT use heapq, collections.deque, bisect, scipy, networkx, sklearn
  or any similar library or module for them.
- Put each data structure in its own file in matchway-backend/app/engine/.
- Add a short comment at the top of each file explaining how the structure works.
- Always verify with "python -m pytest" from the matchway-backend folder. Never run test files directly with python, because that skips tests.

## Data structures (Python backend)
Hash map (rooms, driver state), Queue (drivers at spot), Min-heap (nearest driver),
KD-tree (200 m radius search), Interval tree (time windows), Trie (route matching),
Bipartite graph (driver-rider filtering).

## Working rules
Work only inside this folder. Build one small piece at a time and run it after each step.