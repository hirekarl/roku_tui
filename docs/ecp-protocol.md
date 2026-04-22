# Roku ECP: Under the Hood

The **External Control Protocol (ECP)** is a RESTful API provided by Roku devices to allow remote control over a local network. **roku-tui** is essentially a high-velocity frontend for this protocol.

## 🔌 The Basics

- **Port**: All ECP communication happens on port `8060`.
- **Protocol**: HTTP/1.1.
- **Data Formats**: Requests are usually simple POSTs; responses are typically XML.

---

## ⌨️ Sending Keypresses

To simulate a button press (like "Home" or "Up"), the app sends an empty `POST` request to the following endpoint:
`POST http://<roku-ip>:8060/keypress/<key>`

**Common Key Names**:
- `Home`, `Rev`, `Fwd`, `Play`, `Select`, `Left`, `Right`, `Down`, `Up`, `Back`, `InstantReplay`, `Info`, `Backspace`, `Search`, `Enter`.

---

## 📺 Managing Apps

### Launching an App
`POST http://<roku-ip>:8060/launch/<app-id>`
*Note: You can also pass parameters, which **roku-tui** uses for deep linking (e.g., `?contentId=12345`).*

### Querying Installed Apps
`GET http://<roku-ip>:8060/query/apps`
The Roku returns an XML document listing every installed channel, its ID, name, and version. **roku-tui** parses this XML to enable fuzzy-matching in the `launch` command.

---

## 🔍 Network Inspection

The **Network Panel** in the app shows these requests in real-time. By selecting a row, you can open the **Inspector** to see the raw HTTP exchange:

1.  **Request**: The method (POST/GET), the path, and any headers.
2.  **Response**: The status code (usually `200 OK`) and the XML body.

### Why XML?
Roku's ECP is an older protocol that predates the industry-wide shift to JSON. **roku-tui** automatically converts these XML responses into a readable tree structure in the inspector for easier debugging.

---

## 💡 Educational Value

Because **roku-tui** exposes every request, it's a great tool for learning how APIs work. You can see how a single command like `volume up 5` translates into five distinct HTTP POST requests, each with its own latency and response.
