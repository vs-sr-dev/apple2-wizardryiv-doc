# 05 — The text: a Huffman tree, a message file whose dictionary is written backwards from the end of each block, 424 messages with zero closure failures — and what they say

*Measure: `python tools/wiz4krn.py _work/virt/ASCII.HUFF _work/virt/ASCII.KRN --audit` (notes/wiz4krn-audit.txt), `--dump` (kept in `_work`, not published), `python tools/wiz4krn.py ASCII.HUFF --codes`, census scripts (notes/krn-census.txt, notes/census.txt).*

**The text itself is not published here.** What is published is the format,
the closure, a numbered census of the 424 messages (number, block, lines,
characters — notes/krn-census.txt), and the quotations in this chapter.

## `ASCII.HUFF`: the tree

1,024 bytes, three 256-byte arrays and 256 zeros:

| bytes | array | meaning |
|---|---|---|
| 0..255 | flags[n] | bit 0: the left child of node *n* is a leaf; bit 1: the right child is |
| 256..511 | left[n] | a node index, or the symbol if the flag says leaf |
| 512..767 | right[n] | likewise |
| 768..1023 | — | zero, checked |

Node 0 is the root. 255 internal nodes, **256 leaves — every byte value is a
symbol**, each exactly once (checked), depth 1 to 18. Bits are taken **least
significant first**, and **a 1 goes left**. Both conventions were found by
decoding the first block four ways and keeping the one that produced English
(*"Insert Diskette "A" containing the …"*); nothing else in this chapter would
close under the other three.

One property of the tree is worth writing down because it is wrong for the
file it serves: **the NUL symbol has a one-bit code** — the tree budgets half
of all symbols for it — while NUL is 791 of the 61,501 decoded characters,
**1.29 %**. Space, 9,798 characters (15.9 %), costs five bits. A Huffman tree
built on this text would not look like this one; it was built on something
else, or on more than this.

## `ASCII.KRN`: the message file

118 blocks of 512 bytes. Block 0 opens with two 16-bit words, **116** and
**234**; block 116 is the **index**, and the second word is not resolved.

**The index** (block 116) is 116 ascending words — `1, 62, 124, 185, 209, 235,
276, 304, …, 30250, 30501` — and the sentinel `32767`. Entry *i* is the number
of the first message in text block *i*. Finding message *n* is a binary search
over 116 words and one block read, which is what `HAS.KRNSRCH` — *has kernel
search*, one of the probe-by-filename flags of [03](03-six-sides-and-the-virtual-drive.md)
— tells the program it can do.

**A text block** has lines growing forward from its start (from byte 4 in
block 0) and a dictionary growing backward from its end:

```
byte 511          M, the number of messages in the block
then, M times     [delta]  nlines  size_1 … size_nlines        (read backwards)

  delta  absent for the block's first message, whose number is the index entry;
         one byte, or two when the first has bit 7 set: ((b0 & 0x7F) << 8) | b1
  size   the byte length of each line, length symbol and padding included
```

**A line** starts on a byte boundary: one Huffman symbol giving its length,
then that many Huffman symbols, then zero bits to the next byte. Lines are
Pascal strings; there is no terminator.

How it was found, briefly, because the wrong readings were instructive: a
continuous decode of block 0 was *almost* English — "the{D9}kyve Game you
wish" for "the Save Game you wish" — and the damage always fell where one line
ended and another began. Re-encoding "Save" and searching the bit stream put
it 16 bits after "the": seven zero bits of padding and the nine-bit code for
31, the length of *Save Game you wish to move into*. Then the tail of block 0,
read backwards, turned out to list the measured line sizes — `4 28 25 25 26 23
33 34 31 30` — in order. The two-byte delta was found when blocks 17, 18, 19,
23… ran off their data at a dictionary byte of `128` or more.

### The closure

Every check holds on all 116 text blocks (notes/wiz4krn-audit.txt):

```
text blocks        : 116   index entries 116 + sentinel 32767
messages 424   lines 3175   failures 0
  every line decodes to exactly its dictionary size, to the byte
  the lines tile from the block's text start with no gap
  the lines end before the dictionary begins
  message numbers ascend; each block's first equals its index entry
message numbers 1..30915, 424 distinct
```

And the bytes close: text 53,820 + dictionaries 4,048 + slack 1,520 + header
4 = **59,392 = 116 × 512**; plus the index block and block 117 (512 bytes of
residue from earlier text, never addressed) = **60,416, the file**. Residue 0.

61,501 characters in 53,820 bytes is 7.0 bits a character — the length symbol
and the padding of every line, and a tree fitted to something else, eat most
of what Huffman coding saves.

### Conventions inside the lines

Read from usage, not from code: `^ % # & ?` are substitution slots (`^ tries
to cast a ? but nothing happens!`, `^ ? % and hit # times for & damage`). `~`
is the RETURN key — the character set draws glyph 126 as a return arrow
([06](06-the-data-files.md)) — hence *Press ~*, *L~eave*, *R~un away!*. A
leading `@` (85 lines) opens a new page, a leading `^` (296) marks a
paragraph's last line before a pause, a leading `#` (27) a centred or
emphasised line. **A leading `$` (19 lines) marks an accepted answer** — and
that is how the riddles' solutions come to be readable in this file.

## What the numbers are

| messages | what |
|---|---|
| 1 … 2,650 | the interface, the save-game mover, camp, combat, the summoning pentagram, the opening, the copier, Trebor's ghost, Total Oblivion |
| 5,000 / 5,048 | the 51-line spell table, `NO SPELL` + the 50 spells of *Proving Grounds*; a `*` marks the first spell of each of the 7 mage and 7 priest levels (14) |
| 9,997 … 10,019 | races, alignments, attributes, classes, statuses |
| 11,972 … 12,366 | the Wandering Oracle of Mron and his fortunes |
| 12,983 … 13,479 | **480 monster names**, singular/plural pairs — `Little Old Man / Little Old Men`, `Dink / A Dink`, … `A Demon Lord` |
| 14,002 … 14,214 | **234 item lines**, unidentified/identified pairs — `A STONE / BLOODSTONE`, `A CHARGE CARD / MORDORCHARGE` |
| 14,975 … 26,560 | the story: guardians, rooms, pools, the Temple, Hell, the Cube, the endings |
| 27,984, 28,015 | **the Mordorcharge validation table**: a count (60) and 60 `(code, value)` word pairs ([below](#the-copy-protection-and-the-players-own-copies)) |
| 28,955 … 29,009 | the locate-a-person replies ([below](#the-developers-in-the-locate-spell)) |
| 29,996 … 30,915 | **28 messages of 10-byte binary lines**: five 16-bit words each, many ending `FF FF` — coordinate tables stored *in the message file*, addressed by message number. Their meaning is not resolved |

44 of the 424 messages carry bytes outside printable ASCII; 30 of those are
the binary tables (28 of 10-byte lines, two of mostly 4-byte lines), the rest
carry formatting codes such as the tab that separates an item's two names.

## What they say

The owner knows this game through other people's play. What follows is
selected for the brief — easter eggs, leftovers, and the esoteric layer — and
quoted short.

### The Japanese leftovers, in the American text

Message 1,704:

> NEC 9801 Pascal is (c)1985 by / the Foretune co., ltd. /
> NOTE: if you give characters kanji / names, they will look like tofu on /
> machines without the kanji rom.

Message 2,019 holds a whole language menu — `Select Language: 1) English
2) Kana 3) Kanji` — next to `S)tart Game` and `M)ake Scenario Diskette`. Message
1,629 is the copyright, *"Wizardry is (c)1979-1987 by Andrew Greenberg, Inc.,
and Robert Woodhead, Inc."*, and 2,027 the credit:

> The Return of WERDNA / The Fourth Wizardry Scenario /
> Andrew Greenberg, Robert Woodhead & Roe R. Adams,III.

The NEC message has no reason to be shown on an Apple; nothing here says
whether it can be. It is present, numbered, and indexed.

### The copy protection, and the player's own copies

Message 543: *"Tickets...Tickets, Please! Enter the Validation Code of this
Mordorcharge Card to continue"* — and *"The number you have entered is not
correct. Press ~ to try again."*

**The validation table is in the message file.** Messages 27,984 and 28,015,
two of the "binary" messages, are one table split across a block boundary:
a first line holding the word **60**, then **60 lines of two 16-bit words**,
the first ascending from 1080 to 3996 (notes/mordorcharge.txt). The owner
supplied, from outside these bytes, the table published in *Computist* no. 51
(January 1988) under "Wizardry IV Codes": the game shows three four-digit
numbers and asks for a fourth, and the article gives three columns of twenty
`code-value` pairs — add the three values, subtract 9,000 until four digits
remain. Against it:

```
Computist codes 60, in the game table 60, game codes not in Computist 0
Code #3:  Computist value = (game value + 8449) mod 9000    on 20 of 20
Code #1, Code #2: no (k * game value + c) mod 9000 fits more than 4 and 10 of 20
```

**Every published code is a key of the game's table and nothing else is.**
For the third column the published value is the game's value plus a constant,
exactly, on all twenty. For the first two the relation is not linear in that
sense; the arithmetic that combines the three lives in the p-code and was not
traced, so the article's columns 1 and 2 are confirmed as keys and not yet as
values. The comparison script is `_work/mordorcharge.py` (not published:
it carries the article's table).

The owner also supplied the game's own red-paper booklet, the *Mordor Charge
Valid Card List* — *"Effective Saturday, October 27, A.S.XII, Issue 42,
Netherhell 8"* — whose instructions describe a card number as three groups of
four digits and the validation code as a fourth. Its page of *"Examples of 16
digit format"* uses only codes of the game's table, each group in the same
column role as *Computist*'s (first group from column 1, second from column 2,
third from column 3: 12 of 12). But its twelve example validation codes are
**reproduced by neither** the *Computist* sum (0 of 12) nor any
`(K + Z × value) mod M` of the game's third-column values, for eight moduli
from 8,192 to 65,536, on the six examples that share their first two groups
(notes/mordorcharge.txt). Either the example page is a format illustration and
not a page of valid entries, or the arithmetic is not what either outside
source implies; these bytes cannot decide, and the validation routine in the
p-code was not traced. What the bytes do settle is the vocabulary: the same
60 four-digit codes in the program, the magazine and the booklet. Messages 1,998–2,055 are the `DOCOPY`
segment's script — *Make Scenario Diskette*, one drive or two, *"Before you
play the game, you MUST make copies of each of your Master Diskettes … Make a
copy of Master Diskette "A" first, then "B", etc."* — and 2,019 refuses to
start otherwise: *"You cannot play without making a Scenario Diskette!"*

### The scoring that went by telephone

Messages 1,895–1,949: *"Congratulations on completing one of the endings … On
the following page will be displayed a set of code numbers that measure your
performance … Please call Sir-Tech … Sir-Tech will send you a completion
certificate"*, then *"Your three code numbers are:"*. The Grandmaster text
prints the number itself: `(315)393-6633`.

### The riddles, answered in the file

The Temple's rooms each ask what part of the body a virtue is, in a room of
a colour — and the next line holds the answer behind a `$`:

| message | the being | answer line(s) |
|---|---|---|
| 22,995 | *"I am Attainment … above all the rest, yet beyond mere touch"* | `$CRANIUM` `$BRAIN` |
| 23,088 | a room of *pure soft blue*: *"I am Devotion … the part of the face upon which the Moon doth rise"* | `$LEFT CHEEK` |
| 23,195 | *blood-red crimson*: *"the Virtue of Silence, and the Vice of Avarice"* | `$RIGHT CHEEK` |
| 23,287 | *deep violet*: *"I am Obedience, yet I also beat the Drum of Bigotry"* | `$LEFT ARM` `$LEFT HAND` |
| 23,398 | *orange*: *"I am Courage, but I am also Cruelty"* | `$RIGHT ARM` `$RIGHT HAND` |
| 23,491 | *rose-pink quartz*: *"Within me beats the great heart"* | `$BREAST` `$CHEST` |
| 23,599 | *amber*: *"I am Unselfishness, yet I am Lust"* | `$HIPS` |
| 23,693 | *violet-purple, the Royal Cloth of Tyre* | `$LEGS` |
| 23,785 | *indigo*: *"I am Independence yet I am Idleness"* | `$STOMACH` |
| 23,895 | *deepest yellow*: *"Discrimination at my best, and Avarice at my worst"* | `$FEET` |
| 24,095 | *"Upon what Paths have you trod? Where are you?"* | `$TREE OF LIFE` |

Ten stations, a body from crown to feet, each a virtue paired with its vice,
each in its colour, closing on *the Tree of Life* — and the Oracle's fortunes
say it outright: `LIVE THE QABALAH!`. The other `$` answers are
`$TREBOR SUX` (the Hoplite's password, *"your ancient battlecry"*),
`$MYTHRIL GAUNTLET`/`$MYTHRIL GLOVE` (Master Bertram's question) and `$AMULET`
(*"What do you seek the most, Oh Pilgrim?"*).

### "Have You Forgotten Something?"

The phrase closes four endings and is answered in a fifth. The four: the
**Overlord** (24,498 — *"Long live The Overlord Werdna!!"*) and the three
duels with **Kadorto** — the Green Sword (26,285, you become his statue), the
Blue Sword (26,344, you become a god), the Dragon's Claw (26,398, a god of
*fire, blood and destruction*). Each ends: *"…you wonder… Have You Forgotten
Something?"* **Total Oblivion** (2,104–2,121, *"Press ~ to Rest Forever!"*)
and the plain **Master Adventurer** text (26,540) do not use it.

The one that answers it is the **Dagger of Clear Light**, the *Kris of Truth*
(26,436–26,502), in which Kadorto's head *"pops open, and a singed high Priest
climbs out of a concealed control cabin"*:

> You look back at the temple for a moment, and wonder… / Have You Forgotten
> Something? / You laugh, for you know that you have not.

and confers *Wizardry Grandmaster Adventurer*, followed by seven
postscripts, from *"PS: Have You Forgotten Something?"* and *"PPS: Don't
worry, you haven't."* to *"PPPPPPPS: You have done it all!"*. The Master
Adventurer text (26,540) and its *"what if" nexuses … the great gifts of Lord
Maya* (26,560) follow.

### Lord Hawkwind, and the Dink

Message 24,999:

> Guarding the doorway into the Inner Sanctum of the Temple is Lord Hawkwind
> of Skara Brae, Elfin Ninja--the last member of the Softalk All-Stars.

25,041–25,064 are his responses while you wait — *Reads "Pikestaff"*,
*Answers His Mail*, *Sends Out For Sushi*, *Feeds Sushi To His Dragons*,
*Fills Out Sacrificial Order Form In Triplicate*, *Sacrifices You To Kadorto*
— and 25,135 Kadorto's verdict that you are *"a very poor substitute for a
Goat!"*. Message 87, near the very start of the file, is his end:

> As mighty Achilles fell to Paris' arrow, so does Lord Hawkwind fall to the
> stab of a lowly Dink! Long will Skara Brae be mourning his passing!

and 405 is his book, *"The Chronicles of Hawkwind: 'A really exciting story,
but the ending hasn't been written yet!'"* (the item `IRON BOUND BOOK /
CHRONICLES OF H`). The owner adds, from outside these bytes, that the Dink's
stab is a required step on the road to the Grandmaster ending; the file's
own placement — the Dink among the first monster names (`Dink`, `A Dink`,
12,983) and Hawkwind's death among the first messages — is consistent with a
key that was meant to be hiding in plain sight — and the dungeon itself
spells it: four consecutive level maps carry the letters D, I, N, K
([06](06-the-data-files.md)).

### The developers in the locate spell

Messages 901 (`Locate someone`, `Find whom ? >`, `^ is...`,
`Not on this Scenario Diskette!`) and 28,955–29,009, name and reply:

| you ask for | the answer |
|---|---|
| `WERDNA` | *holding the short end of the stick!* |
| `KADORTO` | *waiting for you!* |
| `ADAMS` | *grinning sardonically!* |
| `WOODHEAD` | *taking a well-deserved vacation!* |
| `GREENBERG` | *counting royalties in the tropics!* |
| `KILROY` | *(or rather, was) here!* |
| `WARTOW` | *saying "I knew that!"* |

Wartow returns as the *"Ron Wartow Not-Yet-Memorial Wading Pool, which is
dedicated to the Elite who jump to brilliant, logical conclusions, but alas,
are wrong!"* (22,348), with a verse from *"the Wartowliedtod"*.

### Quotations and borrowings, as the file has them

* *"No One Expects / The Spanish Inquisition!"* (1,058); the Oracle's
  *"Al'right, it's a fair cop...."* (11,972); `*** KABALAAMMMMOOOO ***` …
  *"3 is too small, and 5 too large / 4 is the number, the number is 4"* (379)
  and the item `HHG OF AUNTY OCK`, whose detonation in Hell (*"…makes one of
  your finest TILTOWAITS look like a wet fire cracker"*) sends you back to
  your Bier.
* The White Rabbit — *"I'm late! I'm late! For the Life of me, where is the
  Opening?"* (409–428); *"Bubble, bubble, toil and trouble"* from a witch who
  explains that the theatrics are *"part of the union contract"* (24,783–24,803).
* *"Enter and Abandon All Hope! (A traditional Intourist greeting)"*,
  *"Dante was here!"*, *"Bring your Marshmallows?"* (16,800–16,899).
* The Cosmic Cube's three doors — *"Ponder upon the ancient mystery of The Lady Or The Tigers"*.
* A charge-card parody in three parts: `MORDORCHARGE`, the Inn's *"Visa,
  Mordor Charge accepted"* under a *"1/2 Star - Mychelyn Guide"*, and the
  Oracle's hotlist — *"Why, it's Captain Thorin's Card!"* — upon which *"Karl
  Maudlin steps from a cable car intoning… 'You won't leave home!'"* (12,242).
* `"CHOMP, CHOMP...EH, WHAT'S EAST, DOC?"`, `A TISKET, A TASKET, TREBOR'S RUMP
  IS IN A BASKET!!!`, `GETOUT JAILFREE`, `HOPALONG CARROT`, `BLADE CUSINART'`,
  `ST.TREBOR RUMP`, *"Trash, trinkets, toys, tribbles, Great Uncle Ted, a Black
  Hole, an old copy of Terror of Tiny Town"* (25,249).
* *"Be Seeing You!"* — on six lines, mostly with `<Cackle>`.
* The Temple of Cant: *"We support the Fundamental Freedom to worship the God
  of *OUR* choice."*

### Names of people

The Castle's encounters are crowded with chivalric orders — the Von Halstern
Chivalry, the Captains' Council, the Ladies of the Rose, the Order of the
Pelican, the Order of the Laurel, the Tyger's Cubs, the Council of Barons,
the Dukes of the Realm (*"Duke Cariadoc of the Bow"* among them) — dozens
of personal names, written as titled personae. The orders' names
are those of the Society for Creative Anachronism's peerages; whether the
names are real members' personas is not something these bytes can show, and
this repository does not try. They are quoted here only as the game prints
them, by message number in notes/krn-census.txt.
