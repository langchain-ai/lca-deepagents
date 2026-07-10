// This lab has no TypeScript port yet.
//
// python/m1/m1.8_hitl_respond.py relies on the "respond" HITL decision type
// (interrupt_on={"ask_user": {"allowed_decisions": ["respond"]}}), which exists
// in the Python langchain package (langchain==1.3.9, DecisionType includes
// "respond" in agents/middleware/human_in_the_loop.py) but is not yet
// implemented in the JS/TS langchain package — checked 1.5.2 (installed),
// 1.5.3 (latest), and the 2.0.0-dev prerelease; DecisionType there is limited
// to ["approve", "edit", "reject"] in all three.
//
// Once "respond" lands in the JS langchain package, port this file to match
// python/m1/m1.8_hitl_respond.py (see typescript/m1/m1.8_hitl.ts for the
// existing approve/edit/reject HITL pattern this would extend).
