# Internal Advanced Audit Policy Category/Sub-Category IDs

The following values are extracted from `ntoskrnl.exe`'s `AdtpGetCategoryAndSubCategoryId` function and `AdtpPerCategoryCount` array.

## Category ID

| ID | Name|
|--|--|
| 0 | System |
| 1 | Logon/Logoff |
| 2 | Object Access |
| 3 | Privilege Use |
| 4 | Detailed Tracking |
| 5 | Policy Change |
| 6 | Account Management |
| 7 | DS Access |
| 8 | Account Logon |

## Sub-Category ID

| ID | Name|
|--|--|
|0 | Security State Change |
|1 | Security System Extension |
|2 | System Integrity |
|3 | IPsec Driver |
|4 | Other System Events |
|5 | Logon |
|6 | Logoff |
|7 | Account Lockout |
|8 | IPsec Main Mode |
|9 | IPsec Quick Mode |
|10 | IPsec Extended Mode |
|11 | Special Logon |
|12 | Other Logon/Logoff Events |
|13 | Network Policy Server |
|14 | User / Device Claims |
|15 | Group Membership |
|16 | File System |
|17 | Registry |
|18 | Kernel Object |
|19 | SAM |
|20 | Certification Services |
|21 | Application Generated |
|22 | File Share |
|23 | Handle Manipulation |
|24 | Filtering Platform Packet Drop |
|25 | Filtering Platform Connection |
|26 | Other Object Access Events |
|27 | Detailed File Share |
|28 | Removable Storage |
|29 | Central Policy Staging |
|30 | Sensitive Privilege Use |
|31 | Non Sensitive Privilege Use |
|32 | Other Privilege Use Events |
|33 | Process Creation |
|34 | Process Termination |
|35 | DPAPI Activity |
|36 | RPC Events |
|37 | Plug and Play Events |
|38 | Token Right Adjusted Events |
|39 | Audit Policy Change |
|40 | Authentication Policy Change |
|41 | Authorization Policy Change |
|42 | MPSSVC Rule-Level Policy Change |
|43 | Filtering Platform Policy Change |
|44 | Other Policy Change Events |
|45 | User Account Management |
|46 | Computer Account Management |
|47 | Security Group Management |
|48 | Distribution Group Management |
|49 | Application Group Management |
|50 | Other Account Management Events |
|51 | Directory Service Access |
|52 | Directory Service Changes |
|53 | Directory Service Replication |
|54 | Detailed Directory Service Replication |
|55 | Credential Validation |
|56 | Kerberos Service Ticket Operations |
|57 | Other Account Logon Events |
