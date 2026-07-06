# Root Cause Analysis (RCA)
## Users Unable to Login to InstaSafe Portal

| **Prepared by** | Sreelakshmi K S |
|-----------------|-----------------|
| **Document Status** | Final |
| **Severity** | P1 — Login Outage |
| **Related Systems** | Keycloak SSO, OpenLDAP |

---

# 1. Incident Summary

Users reported being unable to log in to the InstaSafe Portal. Login attempts either returned a generic **"Authentication failed"** error or remained stuck on the login screen until the request timed out. Some users also reported that the MFA prompt never arrived, even though the username was accepted successfully.

- **Reported by:** Support Desk after receiving multiple similar support tickets within a short period.
- **Affected System:** InstaSafe Portal authentication flow backed by **Keycloak SSO** and **OpenLDAP**.
- **Impact:** All users attempting to log in were affected. No workaround was available because authentication is the single shared login path for the portal.
- **Detection:** Uptime Kuma detected degradation on the Keycloak login endpoint shortly after the first user reports.

---

# 2. Timeline

| Time | Event |
|------|-------|
| **T+0 min** | First support tickets logged reporting login failures. |
| **T+3 min** | Uptime Kuma alert triggered for the Keycloak login endpoint. |
| **T+8 min** | On-call engineer confirmed the portal was reachable, but authentication requests were failing. |
| **T+15 min** | Keycloak logs showed repeated timeouts while querying the OpenLDAP user federation. |
| **T+22 min** | Direct connectivity test from the Keycloak host to the OpenLDAP host on the LDAP port failed. |
| **T+30 min** | Host firewall rules on the OpenLDAP VM were reviewed. A default **REJECT** rule was found without an explicit **ACCEPT** rule for LDAP traffic. |
| **T+38 min** | Missing **ACCEPT** rule was added and verified. Keycloak resumed successful LDAP queries. |
| **T+42 min** | End-to-end login testing, including MFA, succeeded. Incident marked as resolved. |

---

# 3. Five Whys Analysis

### Why 1: Why were users unable to log in?

Because login requests failed during the authentication stage handled by **Keycloak**, not by the portal application itself.

### Why 2: Why was Keycloak unable to authenticate users?

Because Keycloak could not complete its queries against the **OpenLDAP** user directory. Authentication requests timed out instead of receiving responses.

### Why 3: Why were OpenLDAP requests timing out?

Because network connectivity between the **Keycloak host** and the **OpenLDAP host** over the LDAP port was blocked by the host firewall.

### Why 4: Why was the connectivity blocked?

Because a firewall (`iptables`) hardening change introduced a default **REJECT** rule on the OpenLDAP host without adding an explicit **ACCEPT** rule for LDAP traffic.

### Why 5: Why wasn't the missing ACCEPT rule detected before users were impacted?

Because the firewall hardening change was deployed without:

- A pre-change dependency review.
- A post-change validation step.
- Documentation identifying services dependent on the OpenLDAP ports.
- A smoke test of the login flow after deployment.

---

# 4. Root Cause Statement

The immediate technical cause was a missing **ACCEPT** rule for LDAP traffic on the OpenLDAP host, introduced during a firewall hardening change.

The underlying root cause was a **change-management process gap**. Firewall and network changes were being deployed to systems with service dependencies without:

- Performing dependency validation beforehand.
- Executing post-change verification afterward.

This represents a process weakness rather than a one-time configuration error. Similar outages could occur on any dependent service unless the deployment process is improved.

---

# 5. Preventive Actions

## Process Improvements

- Maintain a service dependency map for every host.

  Example:

  ```
  OpenLDAP Host
      ↓
  Keycloak SSO
      ↓
  LDAP Ports: 389 / 636
  ```

- Require a pre-change checklist before any firewall or network modification.

- Require peer review for all `iptables` or security group changes affecting production systems.

- Perform a complete post-change smoke test, including:

  - Portal login
  - Keycloak authentication
  - LDAP lookup
  - MFA verification

before closing the maintenance window.

---

## Monitoring Improvements

- Add a synthetic **Uptime Kuma** monitor that performs a complete login transaction rather than only checking endpoint availability.

- Add **Grafana/Prometheus** alerts specifically for:

  - Keycloak-to-LDAP federation failures
  - LDAP connection timeout rates
  - Authentication error spikes

---

## Documentation Improvements

- Maintain a Git-tracked change log for firewall and network configuration updates to provide rollback history and auditability.

- Document the required open ports for every production host as part of operational documentation and onboarding material.

---

# 6. Lessons Learned

The incident was diagnosed relatively quickly because the symptoms clearly isolated the failure domain:

- The portal remained accessible.
- Authentication consistently failed.
- MFA was never initiated.

These observations immediately indicated that the issue resided within the identity infrastructure rather than the application itself.

The more time-consuming aspect was verifying firewall behavior, as host-level **REJECT** rules silently blocked legitimate traffic without generating obvious application-level errors.

The permanent solution extends beyond restoring a single firewall rule. Future prevention depends on implementing:

- Dependency-aware change management
- Mandatory post-change validation
- Automated authentication smoke tests

These measures will help identify similar issues before they impact users and significantly reduce the risk of authentication outages.
