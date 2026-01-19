# Deployment Checklist

Use this checklist to ensure your autonomous job monitoring agent is properly configured and running.

## Pre-Deployment

- [ ] Python 3.11+ is installed
- [ ] OpenAI API key is configured in environment
- [ ] Outlook/Office 365 email account is ready
- [ ] App Password generated (if using 2FA)
- [ ] All dependencies installed (`pip3 install -r requirements.txt`)

## Configuration

- [ ] Copied `config.env.template` to `config.env`
- [ ] Set `SENDER_EMAIL` in config.env
- [ ] Set `SENDER_PASSWORD` in config.env
- [ ] Set `RECIPIENT_EMAIL` in config.env
- [ ] Verified email credentials are correct
- [ ] Loaded configuration (`source config.env`)

## Testing

- [ ] Ran test suite (`python3 test_workflow.py`)
- [ ] All tests passed successfully
- [ ] Reviewed test digest output (test_digest_output.html)
- [ ] Verified HTML email renders correctly

## Initial Run

- [ ] Started agent in foreground (`python3 main.py`)
- [ ] Observed initial discovery cycle complete
- [ ] Checked for any error messages
- [ ] Verified jobs are being discovered and classified
- [ ] Confirmed database is being populated
- [ ] Stopped agent (Ctrl+C)

## Production Deployment

- [ ] Decided on deployment method (screen or systemd)
- [ ] Started agent in background
- [ ] Verified agent is running (`ps aux | grep main.py`)
- [ ] Checked logs for successful operation
- [ ] Confirmed scheduled tasks are working

## Verification (24 Hours Later)

- [ ] Received daily digest email at 5:00 PM
- [ ] Email contains relevant job listings
- [ ] Jobs are properly categorized
- [ ] Sponsor confidence badges are displayed
- [ ] Application links work correctly
- [ ] No duplicate jobs in digest

## Ongoing Maintenance

- [ ] Monitor database size periodically
- [ ] Check logs for errors weekly
- [ ] Verify email delivery is consistent
- [ ] Update job sources if discovery fails
- [ ] Review and adjust scoring weights as needed

## Troubleshooting Reference

### Email Not Sending
1. Verify SMTP credentials in config.env
2. Check if using App Password for 2FA
3. Test SMTP connection manually
4. Review console error messages

### No Jobs Discovered
1. Check internet connectivity
2. Verify job board HTML structure hasn't changed
3. Review rate limiting delays
4. Consider adding alternative sources

### Agent Stopped Running
1. Check for error messages in logs
2. Verify system resources (memory, disk)
3. Restart agent and monitor
4. Consider using systemd for auto-restart

### Database Issues
1. Check file permissions on jobs.db
2. Verify disk space availability
3. Run integrity check: `sqlite3 jobs.db "PRAGMA integrity_check;"`
4. Backup and recreate if corrupted

## Success Criteria

Your deployment is successful when:

✅ Agent runs continuously without manual intervention
✅ Discovery cycles complete every 6 hours
✅ Daily digest arrives at 5:00 PM
✅ Email contains 0-12 relevant, non-duplicate jobs
✅ Jobs meet all filtering criteria (US, entry-level, H-1B potential)
✅ No errors in console logs
✅ Database grows steadily without issues

## Support

For issues not covered in this checklist, refer to:
- README.md for complete documentation
- QUICKSTART.md for setup guidance
- ARCHITECTURE.md for system design details
- test_workflow.py for validation examples

---

**Deployment Date**: _____________

**Deployed By**: _____________

**Notes**: _____________________________________________
