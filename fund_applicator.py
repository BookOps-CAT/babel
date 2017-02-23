# finds and applies correct fund based on user specified rules
import logging

import babelstore as db

# create logger
module_logger = logging.getLogger('babel_logger.fund')


def find_fund(library_id, funds_str, audn_id, matType_id, location_id):
    # retrieve branch id
    location_record = db.retrieve_record(
        db.Location,
        id=location_id)
    # seprates applied in the form funds
    fund_lst = funds_str.split('+')
    ids = set()

    for fund in fund_lst:
        # print 'fund', fund, 'branch_id', location_record.branch_id
        criteria = {'branch_match': False,
                    'matType_match': False,
                    'audn_match': False}
        fund_record = db.retrieve_record(
            db.Fund,
            library_id=library_id,
            code=fund)
        # fund_record.branches
        # fund_record.matTypes
        # fund_record.audns

        for fund_branch in fund_record.branches:
            if fund_branch.branch_id == location_record.branch_id:
                criteria['branch_match'] = True
                # print 'branch', criteria
        # fund_record = db.retrieve_all(
        #     db.Fund,
        #     'matTypes',
        #     library_id=library_id,
        #     code=fund)
        for fund_matType in fund_record.matTypes:
            if fund_matType.matType_id == matType_id:
                criteria['matType_match'] = True
                # print 'matType', criteria
        # fund_record = db.retrieve_all(
        #     db.Fund,
        #     'audns',
        #     library_id=library_id,
        #     code=fund)
        for fund_audn in fund_record.audns:
            if fund_audn.audn_id == audn_id:
                criteria['audn_match'] = True
                # print 'audn', criteria
        # print 'final', criteria

        if criteria['branch_match'] is True \
            and criteria['matType_match'] is True \
                and criteria['audn_match'] is True:
                ids.add(fund_record.id)

    if len(ids) == 1:
        return (True, list(ids)[0])
    elif len(ids) == 0:
        module_logger.exception(
            "FUND: fund(s) (%s) not applicable for this type of material" % fund_lst)
        return (False, 'not able to correctly aplly one of the funds')
    else:
        module_logger.exception('FUND: applied funds (%s) are not exclusive' % fund_lst)
        return (False, 'multiple fund matches, funds not exclusive')
