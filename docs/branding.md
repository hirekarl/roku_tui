# Branding & Voice

roku-tui's brand identity is deliberately understated. The mascot and voice are present at the edges — in the About modal, the README, the guided tour — and absent from the main interface. Power users never need to acknowledge it; casual users get a personality.

## The Ratatouille Analogy

"roku-tui" sounds like "Ratatouille" when said aloud. The thematic parallel holds up: Remy doesn't replace Linguini — he guides him, runs quietly in the background, and makes him capable of things he couldn't do alone. roku-tui does the same for your Roku. It doesn't surface this analogy explicitly; the mascot's presence is the joke. Anyone who catches it gets a small reward.

## The Mascot

His name is **Ratsmith**. Take 3: forward-facing rat with a chef's toque and wooden spoon, offered toward the viewer. The pose reads as presenting, not performing — confident, not try-hard.

```
          ___
         ( ~ )
          |||
        (\,;,/)
        (o o)\//,     o
         \ /     \,   |
         `+'(  (   \  o
            //  \   |_./
          '~' '~----'

  ascii art by ikas · ascii.co.uk/art/rat
```

**Attribution is required wherever the mascot appears:** `mascot based on ASCII art by ikas · ascii.co.uk/art/rat`

ikas created the original ASCII rat; our design (chef's hat and wooden spoon) is adapted from that work.

Source: https://ascii.co.uk/art/rat

## Tagline

> Precision remote control for people who hate imprecision.

Works for both audiences: casuals read a promise of ease; power users read a technical commitment.

## Voice Principles

**Dry wit over exclamation points.** The voice is confident and direct, occasionally wry. Never breathless.

**Show, don't explain.** Features speak for themselves. Copy names them without narrating them.

**Opt-in personality.** The fun lives in opt-in surfaces (About modal, guided tour, README). The main UI is clean.

**One-liner format.** Any brand copy should be short enough that a power user skips it in under a second but a casual reads it and smiles.

## Copy by Surface

### README hero
```
roku-tui — precision remote control for people who hate imprecision.
```

### About modal (F3)
The mascot appears here as a colophon, styled in a muted color. Copy:

> roku-tui turns your terminal into a full-featured Roku remote —
> deep links, macros, network inspection, YouTube without an API key.
> The things your stock remote pretends it can't do.

### `--help` footer
```
ASCII rat by ikas · ascii.co.uk/art/rat
```

### Guided tour greeting (high personality budget — opt-in surface)
> Welcome. I'm going to show you around — this won't take long,
> and by the end you'll wonder why you ever used the stock remote app.

### Error messages (dry, never panicked)
> No Roku found on the network. Try --ip if you know where it's hiding.

## Dual-Audience Strategy

| Surface | Power user | Casual |
|---|---|---|
| Main UI | No mascot, no personality | Same — earns trust by not being annoying |
| `--help` footer | One-liner, skippable | Small smile + attribution |
| About modal (F3) | Opt-in, fully contained | Delightful |
| Guided tour (F2) | Never opened | Full personality budget |
| README | See it once, move on | First impression, sets tone |
| Error messages | Dry wit, informative | Feels human |

The mascot is a brand element, not a UI element. It never appears in the main interface.
