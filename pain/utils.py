def render_result_codes(result_codes, timeout_count, connection_error_count):
    rc = ""
    for k, v in result_codes.iteritems():
        rc += "%s: %s     " % (k, v)

    if timeout_count > 0:
        rc += 'Timeouts:  %s     ' % timeout_count

    if connection_error_count > 0:
        rc += 'Connection Errors:  %s' % connection_error_count

    rc += '                                            '

    return rc

