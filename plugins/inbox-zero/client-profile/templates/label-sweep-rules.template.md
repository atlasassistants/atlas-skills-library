# Label Sweep Rules

> Defaults set by Atlas. Customized during onboarding. The agent runs the label sweep during the EOD triage and auto-archives items based on these rules.

---

## Active Sweep Rules

| Label | Rule | Agent Action |
|-------|------|-------------|
| **1-Action Required** | Archive once exec has replied (agent checks for outgoing reply in thread) | If no reply after **48 hours** -> re-flag in next SOD report |
| **2-Read Only** | Auto-archive after **48 hours** from labeling | Agent tracks timestamp when label was applied |
| **3-Waiting For** | Check follow-up cadence. If response received -> re-triage. If no response and cadence due -> draft follow-up. If cadence exhausted -> move to 5-Follow Up. | See follow-up cadence rules |
| **4-Delegated** | Archive once the routed team member has replied or confirmed handled | If no activity after **72 hours** -> flag to EA |
| **5-Follow Up** | Stays until actioned. Surfaces in SOD report weekly. | Archive when action completed or exec drops it |
| **0-Leads** | Archive once lead is actioned (call scheduled, declined, or handed off) | Check for calendar event or reply in thread |
| **6, 7, 8** | Auto-archived by filters on arrival - no sweep needed | No agent action required |

---

## Customization Notes

Start with the Atlas defaults above. If the client wants changes, replace this section with the approved custom rules.
