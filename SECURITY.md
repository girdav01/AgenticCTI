# Security Policy

## Overview

AgenticCTI is designed with security as a core principle. This document outlines security best practices, guidelines, and how to report vulnerabilities.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Best Practices

### 1. Credentials Management

**DO:**
- ✅ Store credentials in `.env` file (never commit to git)
- ✅ Use environment variables for all sensitive data
- ✅ Rotate API keys and passwords regularly
- ✅ Use strong, unique passwords
- ✅ For Gmail, use App Passwords instead of account password
- ✅ Limit credential access to necessary personnel only

**DON'T:**
- ❌ Never hardcode credentials in source code
- ❌ Never commit `.env` files to version control
- ❌ Never share credentials in plain text
- ❌ Never use default credentials in production

### 2. API Security

**API Keys:**
- Store all API keys in environment variables
- Use read-only API keys when possible
- Monitor API usage for anomalies
- Implement rate limiting
- Rotate keys regularly

**Endpoint Security:**
- Validate all API endpoints before use
- Use HTTPS for all API communications
- Verify SSL/TLS certificates
- Implement request timeout limits

### 3. Input Validation

All external inputs are validated and sanitized:

```python
# URLs are validated
if not url.startswith(('http://', 'https://')):
    raise ValueError(f"Invalid URL: {url}")

# Content is sanitized
content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)  # Remove control chars
content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
```

**Best Practices:**
- Validate all URLs before scraping
- Sanitize scraped content
- Filter out malicious patterns
- Limit content length
- Validate email addresses
- Check file paths for directory traversal

### 4. Web Scraping Security

**Rate Limiting:**
- Default: 0.5 seconds between requests
- Respects robots.txt by default
- Implements exponential backoff on failures

**User Agent:**
- Identifies as "AgenticCTI/1.0 (Security Research Bot)"
- Can be customized via configuration

**Content Safety:**
- Maximum content length: 50,000 characters
- Minimum content length: 200 characters
- Removes scripts, styles, and executable content

### 5. STIX Data Security

**TLP Markings:**
- Default: TLP:WHITE (public information)
- Configurable per export
- Options: WHITE, GREEN, AMBER, RED

**Data Classification:**
- All CTI data marked with appropriate TLP levels
- Sensitive IOCs can be marked as AMBER or RED
- Export paths secured with proper permissions

### 6. Email Security

**SMTP Security:**
- TLS encryption enabled by default
- Credentials transmitted securely
- Connection timeout: 30 seconds
- Authentication required

**Email Content:**
- No credentials in email body
- Sanitized URLs and content
- HTML content sanitized
- Attachment scanning recommended

### 7. Docker Security

**Container Security:**
- Non-root user execution (`agentic` user)
- Minimal base image (python:3.11-slim)
- No unnecessary packages
- Regular security updates

**Network Security:**
- Isolated bridge network
- Only necessary ports exposed
- Health checks enabled

**Volume Security:**
- Data volumes with appropriate permissions
- Read-only mounts where possible
- No sensitive data in images

### 8. Logging Security

**Log Management:**
- Credentials masked in logs
- Rotating log files (10MB max, 5 backups)
- Log level configurable
- No sensitive data logged

**Sensitive Data Masking:**
```python
# API keys masked: ****abc123
# Passwords not logged
# Email addresses: us****@example.com
```

### 9. Streamlit UI Security

**Authentication:**
- Required by default
- Strong password enforcement
- Session-based authentication
- No password storage in plain text

**Access Control:**
- Sensitive operations require authentication
- Configuration changes logged
- API credentials hidden in UI

### 10. Database Security

**SQLite (if used):**
- File permissions: 600 (owner read/write only)
- Parameterized queries (SQL injection prevention)
- Encrypted at rest (recommended)

## Vulnerability Reporting

### Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

**Email:** security@example.com (replace with actual contact)

**Include:**
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

**Response Time:**
- Initial response: 24-48 hours
- Status update: 7 days
- Fix timeline: Based on severity

### Severity Levels

| Severity | Description | Response Time |
|----------|-------------|---------------|
| Critical | Remote code execution, data breach | 24 hours |
| High | Authentication bypass, privilege escalation | 72 hours |
| Medium | Information disclosure, DoS | 7 days |
| Low | Minor issues, best practice violations | 30 days |

## Security Checklist for Deployment

- [ ] Changed default Streamlit password
- [ ] Configured strong SMTP credentials
- [ ] Set up API keys for CTI platforms
- [ ] Enabled TLS for SMTP
- [ ] Configured firewall rules
- [ ] Set appropriate file permissions
- [ ] Enabled log rotation
- [ ] Reviewed CTI source list
- [ ] Set up monitoring and alerts
- [ ] Configured backup procedures
- [ ] Tested disaster recovery
- [ ] Updated all dependencies
- [ ] Reviewed Docker security settings
- [ ] Implemented rate limiting
- [ ] Set up SSL/TLS for web interface

## Security Updates

**Dependency Updates:**
```bash
# Regular updates
pip install -U -r requirements.txt

# Security-only updates
pip install -U --upgrade-strategy only-if-needed -r requirements.txt
```

**Monitoring:**
- Subscribe to security advisories for dependencies
- Monitor CVE databases for vulnerabilities
- Review OWASP Top 10 regularly
- Audit third-party libraries

## Compliance

### Data Protection

- **GDPR**: No personal data collected without consent
- **CCPA**: User data rights respected
- **Data Retention**: Configurable retention policies

### Threat Intelligence Sharing

- **TLP Protocol**: Followed for all shared intelligence
- **Attribution**: Source attribution maintained
- **Privacy**: No PII in shared intelligence

## Security Features

### Implemented Controls

- ✅ Input validation and sanitization
- ✅ Secure credential management
- ✅ TLS/SSL encryption
- ✅ Rate limiting
- ✅ Authentication and authorization
- ✅ Logging and monitoring
- ✅ Error handling
- ✅ Timeout controls
- ✅ Content filtering
- ✅ API security

### Planned Enhancements

- 🔜 Multi-factor authentication
- 🔜 API authentication tokens
- 🔜 Encrypted database storage
- 🔜 Audit logging
- 🔜 Intrusion detection
- 🔜 Security scanning automation

## Incident Response

### In Case of Security Incident

1. **Contain**: Isolate affected systems
2. **Assess**: Determine scope and impact
3. **Notify**: Report to security team
4. **Remediate**: Apply fixes
5. **Document**: Record incident details
6. **Review**: Post-incident analysis

### Emergency Contacts

- **Security Team**: security@example.com
- **On-Call**: +1-XXX-XXX-XXXX

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls/)
- [STIX 2.1 Security](https://oasis-open.github.io/cti-documentation/)

## Acknowledgments

We thank the security research community for responsible disclosure and continuous improvement of security practices.

---

**Last Updated**: 2024-11-11
**Version**: 1.0.0
