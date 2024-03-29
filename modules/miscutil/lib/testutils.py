## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# pylint: disable=E1102

"""
Helper functions for building and running test suites.
"""

__revision__ = "$Id$"

CFG_TESTUTILS_VERBOSE = 1

import os
import sys
import time
import unittest

from urllib import urlencode
from itertools import chain, repeat

try:
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:
    # web tests will not be available, but unit and regression tests will:
    pass

import invenio
from invenio.config import CFG_SITE_URL, \
     CFG_SITE_SECURE_URL, CFG_LOGDIR
from invenio.w3c_validator import w3c_validate, w3c_errors_to_str, \
     CFG_TESTS_REQUIRE_HTML_VALIDATION

def warn_user_about_tests(test_suite_type='regression'):
    """
    Display a standard warning about running tests that might modify
    user data, and wait for user confirmation, unless --yes-i-know
    was specified in the comman line.
    """

    # Provide a command line option to avoid having to type the
    # confirmation every time during development.
    if '--yes-i-know' in sys.argv:
        return

    if test_suite_type == 'web':
        sys.stderr.write("""\
**********************************************************************
**                                                                  **
**     A B O U T   T H E   W E B   T E S T   S U I T E              **
**                                                                  **
** The web test suite will be launched in Firefox.  You must have   **
** the Selenium IDE extension installed to be able to run the web   **
** test suite.  If you do, please check out the results of the web  **
** test suite in the Selenium IDE window.                           **
**                                                                  **
**********************************************************************

""")

    sys.stderr.write("""\
**********************************************************************
**                                                                  **
**     I M P O R T A N T   W A R N I N G                            **
**                                                                  **
** The %s test suite needs to be run on a clean demo site   **
** that you can obtain by doing:                                    **
**                                                                  **
**    $ inveniocfg --drop-demo-site \                               **
**                 --create-demo-site \                             **
**                 --load-demo-records                              **
**                                                                  **
** Note that DOING THE ABOVE WILL ERASE YOUR ENTIRE DATABASE.       **
**                                                                  **
** In addition, due to the write nature of some of the tests,       **
** the demo DATABASE will be ALTERED WITH JUNK DATA, so that        **
** it is recommended to rebuild the demo site anew afterwards.      **
**                                                                  **
**********************************************************************

Please confirm by typing 'Yes, I know!': """ % test_suite_type)

    answer = raw_input('')
    if answer != 'Yes, I know!':
        sys.stderr.write("Aborted.\n")
        raise SystemExit(0)

    return

def make_test_suite(*test_cases):
    """ Build up a test suite given separate test cases"""
    return unittest.TestSuite([unittest.makeSuite(case, 'test')
                               for case in test_cases])

def run_test_suite(testsuite, warn_user=False):
    """
    Convenience function to embed in test suites.  Run given testsuite
    and eventually ask for confirmation of warn_user is True.
    """
    if warn_user:
        warn_user_about_tests()
    unittest.TextTestRunner(verbosity=2).run(testsuite)

def make_url(path, **kargs):
    """ Helper to generate an absolute invenio URL with query
    arguments"""

    url = CFG_SITE_URL + path

    if kargs:
        url += '?' + urlencode(kargs, doseq=True)

    return url

def make_surl(path, **kargs):
    """ Helper to generate an absolute invenio Secure URL with query
    arguments"""

    url = CFG_SITE_SECURE_URL + path

    if kargs:
        url += '?' + urlencode(kargs, doseq=True)

    return url

class InvenioTestUtilsBrowserException(Exception):
    """Helper exception for the regression test suite browser."""
    pass

def test_web_page_existence(url):
    """
    Test whether URL exists and is well accessible.
    Return True or raise exception in case of problems.
    """
    import mechanize
    browser = mechanize.Browser()
    try:
        browser.open(url)
    except:
        raise
    return True

def test_web_page_content(url,
                          username="guest",
                          password="",
                          expected_text="</html>",
                          unexpected_text="",
                          expected_link_target=None,
                          expected_link_label=None,
                          require_validate_p=CFG_TESTS_REQUIRE_HTML_VALIDATION):
    """Test whether web page URL as seen by user USERNAME contains
       text EXPECTED_TEXT and, eventually, contains a link to
       EXPECTED_LINK_TARGET (if set) labelled EXPECTED_LINK_LABEL (if
       set).  The EXPECTED_TEXT is checked via substring matching, the
       EXPECTED_LINK_TARGET and EXPECTED_LINK_LABEL via exact string
       matching.

       EXPECTED_TEXT, EXPECTED_LINK_LABEL and EXPECTED_LINK_TARGET can
       either be strings or list of strings (in order to check multiple
       values inside same page).

       Before doing the tests, login as USERNAME with password
       PASSWORD.  E.g. interesting values for USERNAME are "guest" or
       "admin".

       Return empty list in case of no problems, otherwise list of error
       messages that may have been encountered during processing of
       page.
    """

    if '--w3c-validate' in sys.argv:
        require_validate_p = True
        sys.stderr.write('Required validation\n')

    error_messages = []
    try:
        import mechanize
    except ImportError:
        return ['ERROR: Cannot import mechanize.']
    browser = mechanize.Browser()
    browser.set_handle_robots(False) # ignore robots.txt, since we test gently
    try:
        # firstly login:
        if username == "guest":
            pass
        else:
            browser.open(CFG_SITE_SECURE_URL + "/youraccount/login")
            browser.select_form(nr=0)
            browser['p_un'] = username
            browser['p_pw'] = password
            browser.submit()
            username_account_page_body = browser.response().read()
            try:
                username_account_page_body.index("You are logged in as %s." % username)
            except ValueError:
                raise InvenioTestUtilsBrowserException, \
                      'ERROR: Cannot login as %s.' % username

        # secondly read page body:
        browser.open(url)
        url_body = browser.response().read()

        # now test for EXPECTED_TEXT:
        # first normalize expected_text
        if isinstance(expected_text, str):
            expected_texts = [expected_text]
        else:
            expected_texts = expected_text
        # then test
        for cur_expected_text in expected_texts:
            try:
                url_body.index(cur_expected_text)
            except ValueError:
                raise InvenioTestUtilsBrowserException, \
                      'ERROR: Page %s (login %s) does not contain %s, but contains %s' % \
                      (url, username, cur_expected_text, url_body)

        # now test for UNEXPECTED_TEXT:
        # first normalize unexpected_text
        if isinstance(unexpected_text, str):
            if unexpected_text:
                unexpected_texts = [unexpected_text]
            else:
                unexpected_texts = []
        else:
            unexpected_texts = unexpected_text
        # then test
        for cur_unexpected_text in unexpected_texts:
            try:
                url_body.index(cur_unexpected_text)
                raise InvenioTestUtilsBrowserException, \
                      'ERROR: Page %s (login %s) contains %s.' % \
                      (url, username, cur_unexpected_text)
            except ValueError:
                pass

        # now test for EXPECTED_LINK_TARGET and EXPECTED_LINK_LABEL:
        if expected_link_target or expected_link_label:
            # first normalize expected_link_target and expected_link_label
            if isinstance(expected_link_target, str) or \
                   expected_link_target is None:
                expected_link_targets = [expected_link_target]
            else:
                expected_link_targets = expected_link_target
            if isinstance(expected_link_label, str) or \
                   expected_link_label is None:
                expected_link_labels = [expected_link_label]
            else:
                expected_link_labels = expected_link_label
            max_links = max(len(expected_link_targets), len(expected_link_labels))
            expected_link_labels = chain(expected_link_labels, repeat(None))
            expected_link_targets = chain(expected_link_targets, repeat(None))
            # then test
            for dummy in range(0, max_links):
                cur_expected_link_target = expected_link_targets.next()
                cur_expected_link_label = expected_link_labels.next()
                try:
                    browser.find_link(url=cur_expected_link_target,
                                      text=cur_expected_link_label)
                except mechanize.LinkNotFoundError:
                    raise InvenioTestUtilsBrowserException, \
                          'ERROR: Page %s (login %s) does not contain link to %s entitled %s.' % \
                          (url, username, cur_expected_link_target, cur_expected_link_label)

        # now test for validation if required
        if require_validate_p:
            valid_p, errors, warnings = w3c_validate(url_body)
            if not valid_p:
                error_text = 'ERROR: Page %s (login %s) does not validate:\n %s' % \
                                  (url, username, w3c_errors_to_str(errors, warnings))
                open('%s/w3c-markup-validator.log' % CFG_LOGDIR, 'a').write(error_text)
                raise InvenioTestUtilsBrowserException, error_text


    except mechanize.HTTPError, msg:
        error_messages.append('ERROR: Page %s (login %s) not accessible. %s' % \
                              (url, username, msg))
    except InvenioTestUtilsBrowserException, msg:
        error_messages.append('ERROR: Page %s (login %s) led to an error: %s.' % \
                              (url, username, msg))

    # logout after tests:
    browser.open(CFG_SITE_SECURE_URL + "/youraccount/logout")
    browser.response().read()
    browser.close()

    if CFG_TESTUTILS_VERBOSE >= 9:
        print "%s test_web_page_content(), tested page `%s', login `%s', expected text `%s', errors `%s'." % \
              (time.strftime("%Y-%m-%d %H:%M:%S -->", time.localtime()),
               url, username, expected_text,
               ",".join(error_messages))

    return error_messages

def merge_error_messages(error_messages):
    """If the ERROR_MESSAGES list is non-empty, merge them and return nicely
       formatted string suitable for printing.  Otherwise return empty
       string.
    """
    out = ""
    if error_messages:
        out = "\n*** " + "\n*** ".join(error_messages)
    return out

def build_and_run_unit_test_suite():
    """
    Detect all Invenio modules with names ending by '*_tests.py' (and
    not '_regression_tests.py'), build a complete test suite of them,
    and run it.  Called by 'inveniocfg --run-unit-tests'.
    """

    # We first import webinterface_tests in order to be sure to have
    # the fake Apache environment loaded among first things.  This is
    # needed for older OSes and mod_pythons such as on SLC4.
#    from invenio import webinterface_tests

    test_modules = []

    for candidate in os.listdir(os.path.dirname(invenio.__file__)):
        base, ext = os.path.splitext(candidate)

        if ext != '.py' or not (base.endswith('_tests') and not \
                                base.endswith('_regression_tests') and not \
                                base.endswith('_web_tests')):
            continue

        module = __import__('invenio.' + base, globals(), locals(), ['TEST_SUITE'])
        test_modules.append(module.TEST_SUITE)

    complete_suite = unittest.TestSuite(test_modules)
    unittest.TextTestRunner(verbosity=2).run(complete_suite)

def build_and_run_regression_test_suite():
    """
    Detect all Invenio modules with names ending by
    '*_regression_tests.py', build a complete test suite of them, and
    run it.  Called by 'inveniocfg --run-regression-tests'.
    """

    test_modules = []

    for candidate in os.listdir(os.path.dirname(invenio.__file__)):
        base, ext = os.path.splitext(candidate)

        if ext != '.py' or not base.endswith('_regression_tests'):
            continue

        module = __import__('invenio.' + base, globals(), locals(), ['TEST_SUITE'])
        test_modules.append(module.TEST_SUITE)

    warn_user_about_tests()

    complete_suite = unittest.TestSuite(test_modules)
    unittest.TextTestRunner(verbosity=2).run(complete_suite)

def build_and_run_web_test_suite():
    """
    Detect all Invenio modules with names ending by
    '*_web_tests.py', build a complete test suite of them, and
    run it.  Called by 'inveniocfg --run-web-tests'.
    """

    test_modules = []

    for candidate in os.listdir(os.path.dirname(invenio.__file__)):
        base, ext = os.path.splitext(candidate)

        if ext != '.py' or not base.endswith('_web_tests'):
            continue

        module = __import__('invenio.' + base, globals(), locals(), ['TEST_SUITE'])
        test_modules.append(module.TEST_SUITE)

    warn_user_about_tests()

    complete_suite = unittest.TestSuite(test_modules)
    unittest.TextTestRunner(verbosity=2).run(complete_suite)


class InvenioWebTestCase(unittest.TestCase):
    """ Helper library of useful web test functions
    for web tests creation.
    """

    def setUp(self):
        """Initialization before tests."""

        # the instance of Firefox WebDriver is created
        self.browser = webdriver.Firefox()
        # list of errors
        self.errors = []

    def tearDown(self):
        """Cleanup actions after tests."""

        self.browser.quit()
        self.assertEqual([], self.errors)

    def find_element_by_name_with_timeout(self, element_name, timeout=30):
        """ Find an element by name. This waits up to 'timeout' seconds
        before throwing an InvenioWebTestCaseException or if it finds the
        element will return it in 0 - timeout seconds.
        @param element_name: name of the element to find
        @type element_name: string
        @param timeout: time in seconds before throwing an exception
        if the element is not found
        @type timeout: int
        """

        try:
            WebDriverWait(self.browser, timeout).until(lambda driver: driver.find_element_by_name(element_name))
        except:
            raise InvenioWebTestCaseException(element=element_name)

    def find_element_by_link_text_with_timeout(self, element_link_text, timeout=30):
        """ Find an element by link text. This waits up to 'timeout' seconds
        before throwing an InvenioWebTestCaseException or if it finds the element
        will return it in 0 - timeout seconds.
        @param element_link_text: link text of the element to find
        @type element_link_text: string
        @param timeout: time in seconds before throwing an exception
        if the element is not found
        @type timeout: int
        """

        try:
            WebDriverWait(self.browser, timeout).until(lambda driver: driver.find_element_by_link_text(element_link_text))
        except:
            raise InvenioWebTestCaseException(element=element_link_text)

    def find_element_by_id_with_timeout(self, element_id, timeout=30):
        """ Find an element by id. This waits up to 'timeout' seconds
        before throwing an InvenioWebTestCaseException or if it finds the element
        will return it in 0 - timeout seconds.
        @param element_id: id of the element to find
        @type element_id: string
        @param timeout: time in seconds before throwing an exception
        if the element is not found
        @type timeout: int
        """

        try:
            WebDriverWait(self.browser, timeout).until(lambda driver: driver.find_element_by_id(element_id))
        except:
            raise InvenioWebTestCaseException(element=element_id)

    def find_element_by_xpath_with_timeout(self, element_xpath, timeout=30):
        """ Find an element by xpath. This waits up to 'timeout' seconds
        before throwing an InvenioWebTestCaseException or if it finds the element
        will return it in 0 - timeout seconds.
        @param element_xpath: xpath of the element to find
        @type element_xpath: string
        @param timeout: time in seconds before throwing an exception
        if the element is not found
        @type timeout: int
        """

        try:
            WebDriverWait(self.browser, timeout).until(lambda driver: driver.find_element_by_xpath(element_xpath))
        except:
            raise InvenioWebTestCaseException(element=element_xpath)

    def find_page_source_with_timeout(self, timeout=30):
        """ Find the page source. This waits up to 'timeout' seconds
        before throwing an InvenioWebTestCaseException
        or if the page source is loaded will return it
        in 0 - timeout seconds.
        @param timeout: time in seconds before throwing an exception
        if the page source is not found
        @type timeout: int
        """

        try:
            WebDriverWait(self.browser, timeout).until(lambda driver: driver.page_source)
        except:
            raise InvenioWebTestCaseException(element="page source")

    def login(self, username="guest", password=""):
        """ Login function
        @param username: the username (nickname or email)
        @type username: string
        @param password: the corresponding password
        @type password: string
        """

        if not "You can use your nickname or your email address to login." in self.browser.page_source:
            if "You are no longer recognized by our system" in self.browser.page_source:
                self.find_element_by_link_text_with_timeout("login here")
                self.browser.find_element_by_link_text("login here").click()
            else:
                self.find_element_by_link_text_with_timeout("login")
                self.browser.find_element_by_link_text("login").click()

        self.find_element_by_name_with_timeout("p_un")
        self.browser.find_element_by_name("p_un").clear()
        self.fill_textbox("p_un", username)
        self.find_element_by_name_with_timeout("p_pw")
        self.browser.find_element_by_name("p_pw").clear()
        self.fill_textbox("p_pw", password)
        self.find_element_by_name_with_timeout("action")
        self.browser.find_element_by_name("action").click()

    def logout(self):
        """ Logout function
        """

        self.find_element_by_link_text_with_timeout("logout")
        self.browser.find_element_by_link_text("logout").click()

    def element_value_test(self, element_name, \
                           expected_element_value="", unexpected_element_value=""):
        """ Function to check if the value in the given
        element is the expected (unexpected) value or not
        @param element_name: name of the corresponding element in the form
        @type element_name: string
        @param expected_element_value: the expected element value
        @type expected_element_value: string
        @param unexpected_element_value: the unexpected element value
        @type unexpected_element_value: string
        """

        self.find_element_by_name_with_timeout(element_name)
        q = self.browser.find_element_by_name(element_name)
        if unexpected_element_value:
            try:
                self.assertNotEqual(q.get_attribute('value'), unexpected_element_value)
            except AssertionError, e:
                self.errors.append(str(e))

        if expected_element_value:
            try:
                self.assertEqual(q.get_attribute('value'), expected_element_value)
            except AssertionError, e:
                self.errors.append(str(e))

    def page_source_test(self, expected_text="", unexpected_text=""):
        """ Function to check if the current page contains
        the expected text (unexpected text) or not.
        The expected text (unexpected text) can also be
        a link.
        The expected text (unexpected text) can be a list of strings
        in order to check multiple values inside same page
        @param expected_text: the expected text
        @type expected_text: string or list of strings
        @param unexpected_text: the unexpected text
        @type unexpected_text: string or list of strings
        """

        self.find_page_source_with_timeout()
        if unexpected_text:
            if isinstance(unexpected_text, str):
                unexpected_texts = [unexpected_text]
            else:
                unexpected_texts = unexpected_text

            for unexpected_text in unexpected_texts:
                try:
                    self.assertEqual(-1, self.browser.page_source.find(unexpected_text))
                except AssertionError, e:
                    self.errors.append(str(e))

        if expected_text:
            if isinstance(expected_text, str):
                expected_texts = [expected_text]
            else:
                expected_texts = expected_text

            for expected_text in expected_texts:
                try:
                    self.assertNotEqual(-1, self.browser.page_source.find(expected_text))
                except AssertionError, e:
                    self.errors.append(str(e))

    def choose_selectbox_option_by_label(self, selectbox_name, label):
        """ Select the option at the given label in
        the corresponding select box
        @param selectbox_name: the name of the corresponding
        select box in the form
        @type selectbox_name: string
        @param label: the option at this label will be selected
        @type label: string
        """

        self.find_element_by_name_with_timeout(selectbox_name)
        selectbox = self.browser.find_element_by_name(selectbox_name)
        options = selectbox.find_elements_by_tag_name("option")
        for option in options:
            if option.text == label:
                option.click()
                break

    def choose_selectbox_option_by_index(self, selectbox_name, index):
        """ Select the option at the given index in
        the corresponding select box
        @param selectbox_name: the name of the corresponding
        select box in the form
        @type selectbox_name: string
        @param index: the option at this index will be selected
        @type index: int
        """

        self.find_element_by_name_with_timeout(selectbox_name)
        selectbox = self.browser.find_element_by_name(selectbox_name)
        options = selectbox.find_elements_by_tag_name("option")
        options[index].click()

    def choose_selectbox_option_by_value(self, selectbox_name, value):
        """ Select the option at the given value in
        the corresponding select box
        @param selectbox_name: the name of the corresponding
        select box in the form
        @type selectbox_name: string
        @param value: the option at this value will be selected
        @type value: string
        """

        self.find_element_by_name_with_timeout(selectbox_name)
        selectbox = self.browser.find_element_by_name(selectbox_name)
        options = selectbox.find_elements_by_tag_name("option")
        for option in options:
            if option.get_attribute('value') == value:
                option.click()
                break

    def fill_textbox(self, textbox_name, text):
        """ Fill in the input textbox or textarea with the given text
        @param textbox_name: the name of the corresponding textbox
        or text area in the form
        @type textbox_name: string
        @param text: the information that the user wants to send
        @type text: string
        """

        self.find_element_by_name_with_timeout(textbox_name)
        textbox = self.browser.find_element_by_name(textbox_name)
        textbox.send_keys(text)

    def handle_popup_dialog(self):
        """ Access the alert after triggering an action
        that opens a popup. """

        try:
            alert = self.browser.switch_to_alert()
            alert.accept()
        except:
            pass


class InvenioWebTestCaseException(Exception):
    """This exception is thrown if the element
    we are looking for is not found after a set time period.
    The element is not found because the page needs more
    time to be fully loaded. To avoid this exception,
    we should increment the time period for that element in
    the corresponding function. See also:
    find_element_by_name_with_timeout()
    find_element_by_link_text_with_timeout()
    find_element_by_id_with_timeout()
    find_element_by_xpath_with_timeout()
    find_page_source_with_timeout()
    """

    def __init__(self, element):
        """Initialisation."""
        self.element = element
        self.message = "Time for finding the element '%s' has expired" % self.element

    def __str__(self):
        """String representation."""
        return repr(self.message)
