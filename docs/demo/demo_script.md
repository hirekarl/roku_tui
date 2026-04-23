# Demo Script: Roku-TUI Presentation

**Duration:** 2.5 - 3 Minutes  
**Tone:** Technical, efficient, "Developer-First"  
**Mascot:** Ratsmith

---

## Phase 1: Problem & Root Cause (0:00 – 0:45)
**Action Beat:** Start on a clean, empty terminal. Have the command `uv run roku-tui` typed out but not yet executed.

**Script:**
"We’ve all been there: You’re deep in a coding session, you want to put something on the TV in the background, and the physical remote is... somewhere. Probably under the couch.

But the real problem isn't just the hardware. The root cause is that most Roku interfaces are built for casual consumers, not power users. They rely on bloated mobile apps or slow on-screen keyboards that abstract away the speed of the protocol. If you’re a developer, you don't want a GUI. You want an endpoint."

---

## Phase 2: The Solution (0:45 – 1:15)
**Action Beat:** Execute `uv run roku-tui --mock`. When the Discovery Screen appears, hover over the mascot art.

**Script:**
"Enter `roku-tui`. This is a high-performance terminal interface built with Python and Textual. It treats your Roku not just as a media device, but as a scriptable server. 

Instead of clicking a D-pad twenty times, we use the Roku External Control Protocol—or ECP—over HTTP. By bringing this into the terminal, we get features that a physical remote can't touch: fuzzy search, command chaining, and real-time network inspection."

---

## Phase 3: Live Demo (1:15 – 2:30)
**Action Beat 1:** Select the mock device. Immediately type `home; launch netflix` in the console.
> "Notice the console at the bottom. I can chain commands with semicolons. One line, two actions. No lag."

**Action Beat 2:** Switch to the Network Panel (`Ctrl+N`). Type `up 3; select`.
> "On the right is our Network Panel. For the first time, you can see the 'guts' of the remote. Every keypress is an async POST request. If you’re debugging a Roku app or an automation script, this data is gold."

**Action Beat 3:** Type `yt search lo-fi beats` then `yt launch 1`.
> "We’ve integrated YouTube directly. I can search, get a results table, and launch a video without ever leaving the keyboard."

**Action Beat 4:** Type `ratsay "That's how we do it."`.
> "And of course, we have Ratsmith—our mascot—who can handle our headless automation or just give us some feedback during the demo."

---

## Phase 4: Conclusion (2:30 – 3:00)
**Action Beat:** Open the About Screen (`F3`) to show the version and the large Ratsmith ASCII art.

**Script:**
"`roku-tui` turns a clumsy consumer experience into a streamlined developer workflow. It’s open-source, it’s built for the terminal, and it’s available now via `uv` or `pip`. 

I’m [Your Name]. Thanks for watching. Ratsmith, take us home."

---

## Recording Checklist
- [ ] **Theme:** Use `roku-night` (default) for best recording contrast.
- [ ] **Font:** Use a clean monospace font (JetBrains Mono, Fira Code).
- [ ] **Mode:** Use `--mock` mode to ensure consistent response times during the demo.
- [ ] **Pacing:** Pause for 1 second after hitting Enter on commands to let the UI feedback register on video.
