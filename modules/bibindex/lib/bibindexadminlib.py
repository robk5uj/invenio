## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Invenio BibIndex Administrator Interface."""

__revision__ = "$Id$"

import random

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_SITE_URL, \
     CFG_BINDIR
from invenio.bibrankadminlib import write_outcome, modify_translations, \
        get_def_name, get_name, get_languages, addadminbox, tupletotable, \
        createhiddenform
from invenio.access_control_engine import acc_authorize_action
from invenio.dbquery import run_sql, get_table_status_info, wash_table_column_name
from invenio.bibindex_engine_stemmer import get_stemming_language_map
import invenio.template
websearch_templates = invenio.template.load('websearch')

def getnavtrail(previous = ''):
    """Get the navtrail"""

    navtrail = """<a class="navtrail" href="%s/help/admin">Admin Area</a> """ % (CFG_SITE_URL,)
    navtrail = navtrail + previous
    return navtrail

def perform_index(ln=CFG_SITE_LANG, mtype='', content=''):
    """start area for modifying indexes
    mtype - the method that called this method.
    content - the output from that method."""

    fin_output = """
    <table>
    <tr>
    <td>0.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/index?ln=%s">Show all</a></small></td>
    <td>1.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/index?ln=%s&amp;mtype=perform_showindexoverview#1">Overview of indexes</a></small></td>
    <td>2.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/index?ln=%s&amp;mtype=perform_editindexes#2">Edit index</a></small></td>
    <td>3.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/index?ln=%s&amp;mtype=perform_addindex#3">Add new index</a></small></td>
    <td>4.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/field?ln=%s">Manage logical fields</a></small></td>
    <td>5.&nbsp;<small><a href="%s/help/admin/bibindex-admin-guide">Guide</a></small></td>
    </tr>
    </table>
    """ % (CFG_SITE_URL, ln, CFG_SITE_URL, ln, CFG_SITE_URL, ln, CFG_SITE_URL, ln, CFG_SITE_URL, ln, CFG_SITE_URL)

    if mtype == "perform_showindexoverview" and content:
        fin_output += content
    elif mtype == "perform_showindexoverview" or not mtype:
        fin_output += perform_showindexoverview(ln, callback='')

    if mtype == "perform_editindexes" and content:
        fin_output += content
    elif mtype == "perform_editindexes" or not mtype:
        fin_output += perform_editindexes(ln, callback='')

    if mtype == "perform_addindex" and content:
        fin_output += content
    elif mtype == "perform_addindex" or not mtype:
        fin_output += perform_addindex(ln, callback='')

    return addadminbox("<b>Menu</b>",  [fin_output])

def perform_field(ln=CFG_SITE_LANG, mtype='', content=''):
    """Start area for modifying fields
    mtype - the method that called this method.
    content - the output from that method."""

    fin_output = """
    <table>
    <tr>
    <td>0.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/field?ln=%s">Show all</a></small></td>
    <td>1.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/field?ln=%s&amp;mtype=perform_showfieldoverview#1">Overview of logical fields</a></small></td>
    <td>2.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/field?ln=%s&amp;mtype=perform_editfields#2">Edit logical field</a></small></td>
    <td>3.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/field?ln=%s&amp;mtype=perform_addfield#3">Add new logical field</a></small></td>
    <td>4.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/index?ln=%s">Manage Indexes</a></small></td>
    <td>5.&nbsp;<small><a href="%s/help/admin/bibindex-admin-guide">Guide</a></small></td>
    </tr>
    </table>
    """ % (CFG_SITE_URL, ln, CFG_SITE_URL, ln, CFG_SITE_URL, ln, CFG_SITE_URL, ln, CFG_SITE_URL, ln, CFG_SITE_URL)

    if mtype == "perform_showfieldoverview" and content:
        fin_output += content
    elif mtype == "perform_showfieldoverview" or not mtype:
        fin_output += perform_showfieldoverview(ln, callback='')

    if mtype == "perform_editfields" and content:
        fin_output += content
    elif mtype == "perform_editfields" or not mtype:
        fin_output += perform_editfields(ln, callback='')

    if mtype == "perform_addfield" and content:
        fin_output += content
    elif mtype == "perform_addfield" or not mtype:
        fin_output += perform_addfield(ln, callback='')

    return addadminbox("<b>Menu</b>",  [fin_output])

def perform_editfield(fldID, ln=CFG_SITE_LANG, mtype='', content='', callback='yes', confirm=-1):
    """form to modify a field. this method is calling other methods which again is calling this and sending back the output of the method.
    if callback, the method will call perform_editcollection, if not, it will just return its output.
    fldID - id of the field
    mtype - the method that called this method.
    content - the output from that method."""

    fld_dict = dict(get_def_name('', "field"))
    if fldID in [-1, "-1"]:
        return addadminbox("Edit logical field",  ["""<b><span class="info">Please go back and select a logical field</span></b>"""])

    fin_output = """
    <table>
    <tr>
    <td><b>Menu</b></td>
    </tr>
    <tr>
    <td>0.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editfield?fldID=%s&amp;ln=%s">Show all</a></small></td>
    <td>1.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editfield?fldID=%s&amp;ln=%s&amp;mtype=perform_modifyfield">Modify field code</a></small></td>
    <td>2.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editfield?fldID=%s&amp;ln=%s&amp;mtype=perform_modifyfieldtranslations">Modify translations</a></small></td>
    <td>3.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editfield?fldID=%s&amp;ln=%s&amp;mtype=perform_modifyfieldtags">Modify MARC tags</a></small></td>
    <td>4.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editfield?fldID=%s&amp;ln=%s&amp;mtype=perform_deletefield">Delete field</a></small></td>
    </tr><tr>
    <td>5.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editfield?fldID=%s&amp;ln=%s&amp;mtype=perform_showdetailsfield">Show field usage</a></small></td>
    </tr>
    </table>
    """ % (CFG_SITE_URL, fldID, ln, CFG_SITE_URL, fldID, ln, CFG_SITE_URL, fldID, ln, CFG_SITE_URL, fldID, ln, CFG_SITE_URL, fldID, ln, CFG_SITE_URL, fldID, ln)

    if mtype == "perform_modifyfield" and content:
        fin_output += content
    elif mtype == "perform_modifyfield" or not mtype:
        fin_output += perform_modifyfield(fldID, ln, callback='')

    if mtype == "perform_modifyfieldtranslations" and content:
        fin_output += content
    elif mtype == "perform_modifyfieldtranslations" or not mtype:
        fin_output += perform_modifyfieldtranslations(fldID, ln, callback='')

    if mtype == "perform_modifyfieldtags" and content:
        fin_output += content
    elif mtype == "perform_modifyfieldtags" or not mtype:
        fin_output += perform_modifyfieldtags(fldID, ln, callback='')

    if mtype == "perform_deletefield" and content:
        fin_output += content
    elif mtype == "perform_deletefield" or not mtype:
        fin_output += perform_deletefield(fldID, ln, callback='')

    return addadminbox("Edit logical field '%s'" % fld_dict[int(fldID)],  [fin_output])

def perform_editindex(idxID, ln=CFG_SITE_LANG, mtype='', content='', callback='yes', confirm=-1):
    """form to modify a index. this method is calling other methods which again is calling this and sending back the output of the method.
    idxID - id of the index
    mtype - the method that called this method.
    content - the output from that method."""

    if idxID in [-1, "-1"]:
        return addadminbox("Edit index",  ["""<b><span class="info">Please go back and select a index</span></b>"""])

    fin_output = """
    <table>
    <tr>
    <td><b>Menu</b></td>
    </tr>
    <tr>
    <td>0.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&amp;ln=%s">Show all</a></small></td>
    <td>1.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&amp;ln=%s&amp;mtype=perform_modifyindex">Modify index name / descriptor</a></small></td>
    <td>2.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&amp;ln=%s&amp;mtype=perform_modifyindextranslations">Modify translations</a></small></td>
    <td>3.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&amp;ln=%s&amp;mtype=perform_modifyindexfields">Modify index fields</a></small></td>
    <td>4.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&amp;ln=%s&amp;mtype=perform_modifyindexstemming">Modify index stemming language</a></small></td>
    <td>5.&nbsp;<small><a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&amp;ln=%s&amp;mtype=perform_deleteindex">Delete index</a></small></td>
    </tr>
    </table>
    """ % (CFG_SITE_URL, idxID, ln, CFG_SITE_URL, idxID, ln, CFG_SITE_URL, idxID, ln, CFG_SITE_URL, idxID, ln, CFG_SITE_URL, idxID, ln, CFG_SITE_URL, idxID, ln)

    if mtype == "perform_modifyindex" and content:
        fin_output += content
    elif mtype == "perform_modifyindex" or not mtype:
        fin_output += perform_modifyindex(idxID, ln, callback='')

    if mtype == "perform_modifyindextranslations" and content:
        fin_output += content
    elif mtype == "perform_modifyindextranslations" or not mtype:
        fin_output += perform_modifyindextranslations(idxID, ln, callback='')

    if mtype == "perform_modifyindexfields" and content:
        fin_output += content
    elif mtype == "perform_modifyindexfields" or not mtype:
        fin_output += perform_modifyindexfields(idxID, ln, callback='')

    if mtype == "perform_modifyindexstemming" and content:
        fin_output += content
    elif mtype == "perform_modifyindexstemming" or not mtype:
        fin_output += perform_modifyindexstemming(idxID, ln, callback='')

    if mtype == "perform_deleteindex" and content:
        fin_output += content
    elif mtype == "perform_deleteindex" or not mtype:
        fin_output += perform_deleteindex(idxID, ln, callback='')

    return addadminbox("Edit index",  [fin_output])

def perform_showindexoverview(ln=CFG_SITE_LANG, callback='', confirm=0):
    subtitle = """<a name="1"></a>1. Overview of indexes"""
    output = """<table cellpadding="3" border="1">"""
    output += """<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>""" % ("ID", "Name", "Fwd.Idx Size", "Rev.Idx Size", "Fwd.Idx Words", "Rev.Idx Records", "Last updated", "Fields", "Translations", "Stemming Language")
    idx = get_idx()
    idx_dict = dict(get_def_name('', "idxINDEX"))

    stemming_language_map = get_stemming_language_map()
    stemming_language_map_reversed = dict([(elem[1], elem[0]) for elem in stemming_language_map.iteritems()])

    for idxID, idxNAME, idxDESC, idxUPD, idxSTEM in idx:
        forward_table_status_info = get_table_status_info('idxWORD%sF' % (idxID < 10 and '0%s' % idxID or idxID))
        reverse_table_status_info = get_table_status_info('idxWORD%sR' % (idxID < 10 and '0%s' % idxID or idxID))
        if str(idxUPD)[-3:] == ".00":
            idxUPD = str(idxUPD)[0:-3]
        lang = get_lang_list("idxINDEXNAME", "id_idxINDEX", idxID)
        idx_fld = get_idx_fld(idxID)
        fld = ""
        for row in idx_fld:
            fld += row[3] + ", "
        if fld.endswith(", "):
            fld = fld[:-2]
        if len(fld) == 0:
            fld = """<strong><span class="info">None</span></strong>"""
        date = (idxUPD and idxUPD or """<strong><span class="info">Not updated</span></strong>""")

        stemming_lang = stemming_language_map_reversed.get(idxSTEM, None)
        if not stemming_lang:
            stemming_lang = """<strong><span class="info">None</span></strong>"""

        if forward_table_status_info and reverse_table_status_info:
            output += """<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>""" % \
                      (idxID,
                       """<a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&amp;ln=%s" title="%s">%s</a>""" % (CFG_SITE_URL, idxID, ln, idxDESC, idx_dict.get(idxID, idxNAME)),
                       "%s MB" % websearch_templates.tmpl_nice_number(forward_table_status_info['Data_length'] / 1048576.0, max_ndigits_after_dot=3),
                       "%s MB" % websearch_templates.tmpl_nice_number(reverse_table_status_info['Data_length'] / 1048576.0, max_ndigits_after_dot=3),
                       websearch_templates.tmpl_nice_number(forward_table_status_info['Rows']),
                       websearch_templates.tmpl_nice_number(reverse_table_status_info['Rows'], max_ndigits_after_dot=3),
                       date,
                       fld,
                       lang,
                       stemming_lang)
        elif not forward_table_status_info:
            output += """<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>""" % \
                      (idxID,
                       """<a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&amp;ln=%s">%s</a>""" % (CFG_SITE_URL, idxID, ln, idx_dict.get(idxID, idxNAME)),
                       "Error", "%s MB" % websearch_templates.tmpl_nice_number(reverse_table_status_info['Data_length'] / 1048576.0, max_ndigits_after_dot=3),
                       "Error",
                       websearch_templates.tmpl_nice_number(reverse_table_status_info['Rows'], max_ndigits_after_dot=3),
                       date,
                       "",
                       lang)
        elif not reverse_table_status_info:
            output += """<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>""" % \
                      (idxID,
                       """<a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&amp;ln=%s">%s</a>""" % (CFG_SITE_URL, idxID, ln, idx_dict.get(idxID, idxNAME)),
                       "%s MB" % websearch_templates.tmpl_nice_number(forward_table_status_info['Data_length'] / 1048576.0, max_ndigits_after_dot=3),
                       "Error", websearch_templates.tmpl_nice_number(forward_table_status_info['Rows'], max_ndigits_after_dot=3),
                       "Error",
                       date,
                       "",
                       lang)
    output += "</table>"

    body = [output]

    if callback:
        return perform_index(ln, "perform_showindexoverview", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_editindexes(ln=CFG_SITE_LANG, callback='yes', content='', confirm=-1):
    """show a list of indexes that can be edited."""

    subtitle = """<a name="2"></a>2. Edit index&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % (CFG_SITE_URL)

    fin_output = ''
    idx = get_idx()
    output = ""
    if len(idx) > 0:
        text = """
        <span class="adminlabel">Index name</span>
        <select name="idxID" class="admin_w200">
        <option value="-1">- Select a index -</option>
        """
        for (idxID, idxNAME, idxDESC, idxUPD, idxSTEM) in idx:
            text += """<option value="%s">%s</option>""" % (idxID, idxNAME)
        text += """</select>"""

        output += createhiddenform(action="%s/admin/bibindex/bibindexadmin.py/editindex" % CFG_SITE_URL,
                                   text=text,
                                   button="Edit",
                                   ln=ln,
                                   confirm=1)

    else:
        output += """No indexes exists"""

    body = [output]

    if callback:
        return perform_index(ln, "perform_editindexes", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_editfields(ln=CFG_SITE_LANG, callback='yes', content='', confirm=-1):
    """show a list of all logical fields that can be edited."""

    subtitle = """<a name="2"></a>2. Edit logical field&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % (CFG_SITE_URL)

    fin_output = ''

    res = get_fld()
    output = ""
    if len(res) > 0:
        text = """
        <span class="adminlabel">Field name</span>
        <select name="fldID" class="admin_w200">
        <option value="-1">- Select a field -</option>
        """
        for (fldID, name, code) in res:
            text += """<option value="%s">%s</option>""" % (fldID, name)
        text += """</select>"""

        output += createhiddenform(action="%s/admin/bibindex/bibindexadmin.py/editfield" % CFG_SITE_URL,
                                   text=text,
                                   button="Edit",
                                   ln=ln,
                                   confirm=1)

    else:
        output += """No logical fields exists"""

    body = [output]

    if callback:
        return perform_field(ln, "perform_editfields", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_addindex(ln=CFG_SITE_LANG, idxNAME='', callback="yes", confirm=-1):
    """form to add a new index.
    idxNAME - the name of the new index"""

    output = ""
    subtitle = """<a name="3"></a>3. Add new index"""
    text = """
    <span class="adminlabel">Index name</span>
    <input class="admin_w200" type="text" name="idxNAME" value="%s" /><br />
    """ % idxNAME
    output = createhiddenform(action="%s/admin/bibindex/bibindexadmin.py/addindex" % CFG_SITE_URL,
                              text=text,
                              ln=ln,
                              button="Add index",
                              confirm=1)
    if idxNAME and confirm in ["1", 1]:
        res = add_idx(idxNAME)
        output += write_outcome(res) + """<br /><a href="%s/admin/bibindex/bibindexadmin.py/editindex?idxID=%s&ln=%s">Configure this index</a>.""" % (CFG_SITE_URL, res[1], ln)
    elif confirm not in ["-1", -1]:
        output += """<b><span class="info">Please give the index a name.</span></b>
        """

    body = [output]

    if callback:
        return perform_index(ln, "perform_addindex", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifyindextranslations(idxID, ln=CFG_SITE_LANG, sel_type='', trans=[], confirm=-1, callback='yes'):
    """Modify the translations of a index
    sel_type - the nametype to modify
    trans - the translations in the same order as the languages from get_languages()"""

    output = ''
    subtitle = ''
    langs = get_languages()
    if confirm in ["2", 2] and idxID:
        finresult = modify_translations(idxID, langs, sel_type, trans, "idxINDEX")
    idx_dict = dict(get_def_name('', "idxINDEX"))
    if idxID and idx_dict.has_key(int(idxID)):
        idxID = int(idxID)
        subtitle = """<a name="2"></a>2. Modify translations for index.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % CFG_SITE_URL

        if type(trans) is str:
            trans = [trans]
        if sel_type == '':
            sel_type = get_idx_nametypes()[0][0]

        header = ['Language', 'Translation']
        actions = []

        types = get_idx_nametypes()
        if len(types) > 1:
            text  = """
            <span class="adminlabel">Name type</span>
            <select name="sel_type" class="admin_w200">
            """

            for (key, value) in types:
                text += """<option value="%s" %s>%s""" % (key, key == sel_type and 'selected="selected"' or '', value)
                trans_names = get_name(idxID, ln, key, "field")
                if trans_names and trans_names[0][0]:
                    text += ": %s" % trans_names[0][0]
                text += "</option>"
            text += """</select>"""

            output += createhiddenform(action="modifyindextranslations#2",
                                       text=text,
                                       button="Select",
                                       idxID=idxID,
                                       ln=ln,
                                       confirm=0)


        if confirm in [-1, "-1", 0, "0"]:
            trans = []
            for (key, value) in langs:
                try:
                    trans_names = get_name(idxID, key, sel_type, "idxINDEX")
                    trans.append(trans_names[0][0])
                except StandardError, e:
                    trans.append('')

        for nr in range(0,len(langs)):
            actions.append(["%s %s" % (langs[nr][1], (langs[nr][0]==CFG_SITE_LANG and '<small>(def)</small>' or ''))])
            actions[-1].append('<input type="text" name="trans" size="30" value="%s"/>' % trans[nr])

        text = tupletotable(header=header, tuple=actions)
        output += createhiddenform(action="modifyindextranslations#2",
                                   text=text,
                                   button="Modify",
                                   idxID=idxID,
                                   sel_type=sel_type,
                                   ln=ln,
                                   confirm=2)

        if sel_type and len(trans):
            if confirm in ["2", 2]:
                output += write_outcome(finresult)

    body = [output]

    if callback:
        return perform_editindex(idxID, ln, "perform_modifyindextranslations", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifyfieldtranslations(fldID, ln=CFG_SITE_LANG, sel_type='', trans=[], confirm=-1, callback='yes'):
    """Modify the translations of a field
    sel_type - the nametype to modify
    trans - the translations in the same order as the languages from get_languages()"""

    output = ''
    subtitle = ''
    langs = get_languages()
    if confirm in ["2", 2] and fldID:
        finresult = modify_translations(fldID, langs, sel_type, trans, "field")
    fld_dict = dict(get_def_name('', "field"))
    if fldID and fld_dict.has_key(int(fldID)):
        fldID = int(fldID)
        subtitle = """<a name="3"></a>3. Modify translations for logical field '%s'&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % (fld_dict[fldID], CFG_SITE_URL)

        if type(trans) is str:
            trans = [trans]
        if sel_type == '':
            sel_type = get_fld_nametypes()[0][0]

        header = ['Language', 'Translation']
        actions = []

        types = get_fld_nametypes()
        if len(types) > 1:
            text  = """
            <span class="adminlabel">Name type</span>
            <select name="sel_type" class="admin_w200">
            """
            for (key, value) in types:
                text += """<option value="%s" %s>%s""" % (key, key == sel_type and 'selected="selected"' or '', value)
                trans_names = get_name(fldID, ln, key, "field")
                if trans_names and trans_names[0][0]:
                    text += ": %s" % trans_names[0][0]
                text += "</option>"
            text += """</select>"""

            output += createhiddenform(action="modifyfieldtranslations#3",
                                       text=text,
                                       button="Select",
                                       fldID=fldID,
                                       ln=ln,
                                       confirm=0)


        if confirm in [-1, "-1", 0, "0"]:
            trans = []
            for (key, value) in langs:
                try:
                    trans_names = get_name(fldID, key, sel_type, "field")
                    trans.append(trans_names[0][0])
                except StandardError, e:
                    trans.append('')

        for nr in range(0,len(langs)):
            actions.append(["%s %s" % (langs[nr][1], (langs[nr][0]==CFG_SITE_LANG and '<small>(def)</small>' or ''))])
            actions[-1].append('<input type="text" name="trans" size="30" value="%s"/>' % trans[nr])

        text = tupletotable(header=header, tuple=actions)
        output += createhiddenform(action="modifyfieldtranslations#3",
                                   text=text,
                                   button="Modify",
                                   fldID=fldID,
                                   sel_type=sel_type,
                                   ln=ln,
                                   confirm=2)

        if sel_type and len(trans):
            if confirm in ["2", 2]:
                output += write_outcome(finresult)

    body = [output]

    if callback:
        return perform_editfield(fldID, ln, "perform_modifytranslations", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_showdetailsfieldtag(fldID, tagID, ln=CFG_SITE_LANG, callback="yes", confirm=-1):
    """form to add a new field.
    fldNAME - the name of the new field
    code - the field code"""

    fld_dict = dict(get_def_name('', "field"))
    fldID = int(fldID)
    tagname = run_sql("SELECT name from tag where id=%s", (tagID, ))[0][0]

    output = ""
    subtitle = """<a name="4.1"></a>Showing details for MARC tag '%s'""" % tagname

    output += "<br /><b>This MARC tag is used directly in these logical fields:</b>&nbsp;"
    fld_tag = get_fld_tags('', tagID)
    exist = {}
    for (id_field,id_tag, tname, tvalue, score) in fld_tag:
        output += "%s, " % fld_dict[int(id_field)]
        exist[id_field] = 1

    output += "<br /><b>This MARC tag is used indirectly in these logical fields:</b>&nbsp;"
    tag = run_sql("SELECT value from tag where id=%s", (id_tag, ))
    tag = tag[0][0]
    for i in range(0, len(tag) - 1):
        res = run_sql("SELECT id_field,id_tag FROM field_tag,tag WHERE tag.id=field_tag.id_tag AND tag.value=%s", ('%' + tag[0:i] + '%',))
        for (id_field, id_tag) in res:
            output += "%s, " % fld_dict[int(id_field)]
            exist[id_field] = 1

    res = run_sql("SELECT id_field,id_tag FROM field_tag,tag WHERE tag.id=field_tag.id_tag AND tag.value like %s", (tag, ))
    for (id_field, id_tag) in res:
        if not exist.has_key(id_field):
            output += "%s, " % fld_dict[int(id_field)]

    body = [output]

    if callback:
        return perform_modifyfieldtags(fldID, ln, "perform_showdetailsfieldtag", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_showdetailsfield(fldID, ln=CFG_SITE_LANG, callback="yes", confirm=-1):
    """form to add a new field.
    fldNAME - the name of the new field
    code - the field code"""

    fld_dict = dict(get_def_name('', "field"))
    col_dict = dict(get_def_name('', "collection"))
    fldID = int(fldID)
    col_fld = get_col_fld('', '', fldID)
    sort_types = dict(get_sort_nametypes())

    fin_output = ""
    subtitle = """<a name="1"></a>5. Show usage for logical field '%s'""" % fld_dict[fldID]

    output = "This logical field is used in these collections:<br />"
    ltype = ''
    exist = {}
    for (id_collection, id_field, id_fieldvalue, ftype, score, score_fieldvalue) in col_fld:
        if ltype != ftype:
            output += "<br /><b>%s:&nbsp;</b>" % sort_types[ftype]
            ltype = ftype
            exist = {}
        if not exist.has_key(id_collection):
            output += "%s, " % col_dict[int(id_collection)]
        exist[id_collection] = 1

    if not col_fld:
        output = "This field is not used by any collections."
    fin_output = addadminbox('Collections', [output])

    body = [fin_output]

    if callback:
        return perform_editfield(ln, "perform_showdetailsfield", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)


def perform_addfield(ln=CFG_SITE_LANG, fldNAME='', code='', callback="yes", confirm=-1):
    """form to add a new field.
    fldNAME - the name of the new field
    code - the field code"""

    output = ""
    subtitle = """<a name="3"></a>3. Add new logical field"""
    code = str.replace(code,' ', '')
    text = """
    <span class="adminlabel">Field name</span>
    <input class="admin_w200" type="text" name="fldNAME" value="%s" /><br />
    <span class="adminlabel">Field code</span>
    <input class="admin_w200" type="text" name="code" value="%s" /><br />
    """ % (fldNAME, code)
    output = createhiddenform(action="%s/admin/bibindex/bibindexadmin.py/addfield" % CFG_SITE_URL,
                              text=text,
                              ln=ln,
                              button="Add field",
                              confirm=1)
    if fldNAME and code and confirm in ["1", 1]:
        res = add_fld(fldNAME, code)
        output += write_outcome(res)
    elif confirm not in ["-1", -1]:
        output += """<b><span class="info">Please give the logical field a name and code.</span></b>
        """

    body = [output]

    if callback:
        return perform_field(ln, "perform_addfield", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_deletefield(fldID, ln=CFG_SITE_LANG, callback='yes', confirm=0):
    """form to remove a field.
    fldID - the field id from table field.
    """

    fld_dict = dict(get_def_name('', "field"))
    if not fld_dict.has_key(int(fldID)):
        return """<b><span class="info">Field does not exist</span></b>"""

    subtitle = """<a name="4"></a>4. Delete the logical field '%s'&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % (fld_dict[int(fldID)], CFG_SITE_URL)
    output  = ""

    if fldID:
        fldID = int(fldID)
        if confirm in ["0", 0]:
            check = run_sql("SELECT id_field from idxINDEX_field where id_field=%s", (fldID, ))
            text = ""
            if check:
                text += """<b><span class="info">This field is used in an index, deletion may cause problems.</span></b><br />"""
            text += """Do you want to delete the logical field '%s' and all its relations and definitions.""" % (fld_dict[fldID])
            output += createhiddenform(action="deletefield#4",
                                       text=text,
                                       button="Confirm",
                                       fldID=fldID,
                                       confirm=1)
        elif confirm in ["1", 1]:
            res = delete_fld(fldID)
            if res[0] == 1:
                return """<br /><b><span class="info">Field deleted.</span></b>""" + write_outcome(res)
            else:
                output += write_outcome(res)

    body = [output]

    if callback:
        return perform_editfield(fldID, ln, "perform_deletefield", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_deleteindex(idxID, ln=CFG_SITE_LANG, callback='yes', confirm=0):
    """form to delete an index.
    idxID - the index id from table idxINDEX.
    """

    if idxID:
        subtitle = """<a name="5"></a>5. Delete the index.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % CFG_SITE_URL
        output  = ""

        if confirm in ["0", 0]:
            idx = get_idx(idxID)
            if idx:
                text = ""
                text += """<b><span class="info">By deleting an index, you may also loose any indexed data in the forward and reverse table for this index.</span></b><br />"""
                text += """Do you want to delete the index '%s' and all its relations and definitions.""" % (idx[0][1])
                output += createhiddenform(action="deleteindex#5",
                                       text=text,
                                       button="Confirm",
                                       idxID=idxID,
                                       confirm=1)
            else:
                return """<br /><b><span class="info">Index specified does not exist.</span></b>"""
        elif confirm in ["1", 1]:
            res = delete_idx(idxID)
            if res[0] == 1:
                return """<br /><b><span class="info">Index deleted.</span></b>""" + write_outcome(res)
            else:
                output += write_outcome(res)

    body = [output]

    if callback:
        return perform_editindex(idxID, ln, "perform_deleteindex", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_showfieldoverview(ln=CFG_SITE_LANG, callback='', confirm=0):
    subtitle = """<a name="1"></a>1. Logical fields overview"""
    output = """<table cellpadding="3" border="1">"""
    output += """<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>""" % ("Field", "MARC Tags", "Translations")
    query = "SELECT id,name FROM field"
    res = run_sql(query)
    col_dict = dict(get_def_name('', "collection"))
    fld_dict = dict(get_def_name('', "field"))

    for field_id,field_name in res:
        query = "SELECT tag.value FROM tag, field_tag WHERE tag.id=field_tag.id_tag AND field_tag.id_field=%s ORDER BY field_tag.score DESC,tag.value ASC"
        res = run_sql(query, (field_id, ))
        field_tags = ""
        for row in res:
            field_tags = field_tags + row[0] + ", "
        if field_tags.endswith(", "):
            field_tags = field_tags[:-2]
        if not field_tags:
            field_tags = """<b><span class="info">None</span></b>"""

        lang = get_lang_list("fieldname", "id_field", field_id)
        output += """<tr><td>%s</td><td>%s</td><td>%s</td></tr>""" % ("""<a href="%s/admin/bibindex/bibindexadmin.py/editfield?fldID=%s&ln=%s">%s</a>""" % (CFG_SITE_URL, field_id, ln, fld_dict[field_id]), field_tags, lang)
    output += "</table>"

    body = [output]

    if callback:
        return perform_field(ln, "perform_showfieldoverview", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifyindex(idxID, ln=CFG_SITE_LANG, idxNAME='', idxDESC='', callback='yes', confirm=-1):
    """form to modify an index name.
    idxID - the index name to change.
    idxNAME - new name of index
    idxDESC - description of index content"""

    subtitle  = ""
    output  = ""
    idx = get_idx(idxID)
    if not idx:
        idxID = -1
    if idxID not in [-1, "-1"]:
        subtitle = """<a name="2"></a>1. Modify index name.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % CFG_SITE_URL
        if confirm in [-1, "-1"]:
            idxNAME = idx[0][1]
            idxDESC = idx[0][2]
        text = """
        <span class="adminlabel">Index name</span>
        <input class="admin_w200" type="text" name="idxNAME" value="%s" /><br />
        <span class="adminlabel">Index description</span>
        <textarea class="admin_w200" name="idxDESC">%s</textarea><br />
        """ % (idxNAME, idxDESC)

        output += createhiddenform(action="modifyindex#1",
                                   text=text,
                                   button="Modify",
                                   idxID=idxID,
                                   ln=ln,
                                   confirm=1)

        if idxID > -1 and idxNAME and confirm in [1, "1"]:
            res = modify_idx(idxID, idxNAME, idxDESC)
            output += write_outcome(res)
        elif confirm in [1, "1"]:
            output += """<br /><b><span class="info">Please give a name for the index.</span></b>"""
    else:
        output  = """No index to modify."""

    body = [output]

    if callback:
        return perform_editindex(idxID, ln, "perform_modifyindex", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifyindexstemming(idxID, ln=CFG_SITE_LANG, idxSTEM='', callback='yes', confirm=-1):
    """form to modify an index name.
    idxID - the index name to change.
    idxSTEM - new stemming language code"""

    subtitle  = ""
    output  = ""

    stemming_language_map = get_stemming_language_map()
    stemming_language_map['None'] = ''

    idx = get_idx(idxID)
    if not idx:
        idxID = -1
    if idxID not in [-1, "-1"]:
        subtitle = """<a name="4"></a>4. Modify index stemming language.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % CFG_SITE_URL
        if confirm in [-1, "-1"]:
            idxSTEM = idx[0][4]
        if not idxSTEM:
            idxSTEM = ''

        language_html_element = """<select name="idxSTEM" class="admin_w200">"""
        languages = stemming_language_map.keys()
        languages.sort()
        for language in languages:
            if stemming_language_map[language] == idxSTEM:
                selected = 'selected="selected"'
            else:
                selected = ""
            language_html_element += """<option value="%s" %s>%s</option>""" % (stemming_language_map[language], selected, language)
        language_html_element += """</select>"""

        text = """
        <span class="adminlabel">Index stemming language</span>
        """ + language_html_element

        output += createhiddenform(action="modifyindexstemming#4",
                                   text=text,
                                   button="Modify",
                                   idxID=idxID,
                                   ln=ln,
                                   confirm=0)

        if confirm in [0, "0"] and get_idx(idxID)[0][4] == idxSTEM:
            output += """<span class="info">Stemming language has not been changed</span>"""
        elif confirm in [0, "0"]:
            text = """
            <span class="important">You are going to change the stemming language for this index. Please note you should not enable stemming for structured-data indexes like "report number", "year", "author" or "collection". On the contrary, it is advisable to enable stemming for indexes like "fulltext", "abstract", "title", etc. since this would improve retrieval quality. <br /> Beware that after changing the stemming language of an index you will have to reindex it. It is a good idea to change the stemming language and to reindex during low usage hours of your service, since searching will be not functional until the reindexing will be completed</span>.<br /> <strong>Are you sure you want to change the stemming language of this index?</strong>"""
            output += createhiddenform(action="modifyindexstemming#4",
                                   text=text,
                                   button="Modify",
                                   idxID=idxID,
                                   idxSTEM=idxSTEM,
                                   ln=ln,
                                   confirm=1)
        elif idxID > -1 and confirm in [1, "1"]:
            res = modify_idx_stemming(idxID, idxSTEM)
            output += write_outcome(res)
            output += """<br /><span class="info">Please note you must run as soon as possible:
            <pre>$> %s/bibindex --reindex -w %s</pre></span>
            """ % (CFG_BINDIR, get_idx(idxID)[0][1])
        elif confirm in [1, "1"]:
            output += """<br /><b><span class="info">Please give a name for the index.</span></b>"""
    else:
        output  = """No index to modify."""

    body = [output]

    if callback:
        return perform_editindex(idxID, ln, "perform_modifyindexstemming", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)


def perform_modifyfield(fldID, ln=CFG_SITE_LANG, code='', callback='yes', confirm=-1):
    """form to modify a field.
    fldID - the field to change."""

    subtitle  = ""
    output  = ""

    fld_dict = dict(get_def_name('', "field"))

    if fldID not in [-1, "-1"]:
        if confirm in [-1, "-1"]:
            res = get_fld(fldID)
            code = res[0][2]
        else:
            code = str.replace("%s" % code, " ", "")
        fldID = int(fldID)
        subtitle = """<a name="2"></a>1. Modify field code for logical field '%s'&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % (fld_dict[int(fldID)], CFG_SITE_URL)

        text = """
        <span class="adminlabel">Field code</span>
        <input class="admin_w200" type="text" name="code" value="%s" /><br />
        """ % code

        output += createhiddenform(action="modifyfield#2",
                                   text=text,
                                   button="Modify",
                                   fldID=fldID,
                                   ln=ln,
                                   confirm=1)

        if fldID > -1 and confirm in [1, "1"]:
            fldID = int(fldID)
            res = modify_fld(fldID, code)
            output += write_outcome(res)
    else:
        output  = """No field to modify.
        """

    body = [output]

    if callback:
        return perform_editfield(fldID, ln, "perform_modifyfield", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifyindexfields(idxID, ln=CFG_SITE_LANG, callback='yes', content='', confirm=-1):
    """Modify which logical fields to use in this index.."""

    output = ''
    subtitle = """<a name="3"></a>3. Modify index fields.&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % CFG_SITE_URL

    output = """<dl>
     <dt>Menu</dt>
     <dd><a href="%s/admin/bibindex/bibindexadmin.py/addindexfield?idxID=%s&amp;ln=%s#3.1">Add field to index</a></dd>
     <dd><a href="%s/admin/bibindex/bibindexadmin.py/field?ln=%s">Manage fields</a></dd>
    </dl>
    """  % (CFG_SITE_URL, idxID, ln, CFG_SITE_URL, ln)

    header = ['Field', '']
    actions = []

    idx_fld = get_idx_fld(idxID)
    if len(idx_fld) > 0:
        for (idxID, idxNAME,fldID, fldNAME, regexp_punct, regexp_alpha_sep) in idx_fld:
            actions.append([fldNAME])
            for col in [(('Remove','removeindexfield'),)]:
                actions[-1].append('<a href="%s/admin/bibindex/bibindexadmin.py/%s?idxID=%s&amp;fldID=%s&amp;ln=%s#3.1">%s</a>' % (CFG_SITE_URL, col[0][1], idxID, fldID, ln, col[0][0]))
                for (str, function) in col[1:]:
                    actions[-1][-1] += ' / <a href="%s/admin/bibindex/bibindexadmin.py/%s?fldID=%s&amp;flID=%s&amp;ln=%s#4.1">%s</a>' % (CFG_SITE_URL, function, idxID, fldID, ln, str)
        output += tupletotable(header=header, tuple=actions)
    else:
        output += """No index fields exists"""

    output += content

    body = [output]

    if callback:
        return perform_editindex(idxID, ln, "perform_modifyindexfields", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifyfieldtags(fldID, ln=CFG_SITE_LANG, callback='yes', content='', confirm=-1):
    """show the sort fields of this collection.."""

    output = ''

    fld_dict = dict(get_def_name('', "field"))
    fld_type = get_fld_nametypes()
    fldID = int(fldID)

    subtitle = """<a name="4"></a>3. Modify MARC tags for the logical field '%s'&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibindex-admin-guide">?</a>]</small>""" % (fld_dict[int(fldID)], CFG_SITE_URL)
    output = """<dl>
     <dt>Menu</dt>
     <dd><a href="%s/admin/bibindex/bibindexadmin.py/addtag?fldID=%s&amp;ln=%s#4.1">Add MARC tag</a></dd>
     <dd><a href="%s/admin/bibindex/bibindexadmin.py/deletetag?fldID=%s&amp;ln=%s#4.1">Delete unused MARC tags</a></dd>
    </dl>
    """  % (CFG_SITE_URL, fldID, ln, CFG_SITE_URL, fldID, ln)

    header = ['', 'Value', 'Comment', 'Actions']
    actions = []

    res = get_fld_tags(fldID)
    if len(res) > 0:
        i = 0
        for (fldID, tagID, tname, tvalue, score) in res:
            move = ""
            if i != 0:
                move += """<a href="%s/admin/bibindex/bibindexadmin.py/switchtagscore?fldID=%s&amp;id_1=%s&amp;id_2=%s&amp;ln=%s&amp=rand=%s#4"><img border="0" src="%s/img/smallup.gif" title="Move tag up"></a>""" % (CFG_SITE_URL, fldID, tagID, res[i - 1][1], ln, random.randint(0, 1000), CFG_SITE_URL)
            else:
                move += "&nbsp;&nbsp;&nbsp;"
            i += 1
            if i != len(res):
                move += '<a href="%s/admin/bibindex/bibindexadmin.py/switchtagscore?fldID=%s&amp;id_1=%s&amp;id_2=%s&amp;ln=%s&amp;rand=%s#4"><img border="0" src="%s/img/smalldown.gif" title="Move tag down"></a>' % (CFG_SITE_URL, fldID, tagID, res[i][1], ln, random.randint(0, 1000), CFG_SITE_URL)

            actions.append([move, tvalue, tname])
            for col in [(('Details','showdetailsfieldtag'), ('Modify','modifytag'),('Remove','removefieldtag'),)]:
                actions[-1].append('<a href="%s/admin/bibindex/bibindexadmin.py/%s?fldID=%s&amp;tagID=%s&amp;ln=%s#4.1">%s</a>' % (CFG_SITE_URL, col[0][1], fldID, tagID, ln, col[0][0]))
                for (str, function) in col[1:]:
                    actions[-1][-1] += ' / <a href="%s/admin/bibindex/bibindexadmin.py/%s?fldID=%s&amp;tagID=%s&amp;ln=%s#4.1">%s</a>' % (CFG_SITE_URL, function, fldID, tagID, ln, str)
        output += tupletotable(header=header, tuple=actions)
    else:
        output += """No fields exists"""

    output += content

    body = [output]

    if callback:
        return perform_editfield(fldID, ln, "perform_modifyfieldtags", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)


def perform_addtag(fldID, ln=CFG_SITE_LANG, value=['',-1], name='', callback="yes", confirm=-1):
    """form to add a new field.
    fldNAME - the name of the new field
    code - the field code"""

    output = ""
    subtitle = """<a name="4.1"></a>Add MARC tag to logical field"""
    text = """
    Add new tag:<br />
    <span class="adminlabel">Tag value</span>
    <input class="admin_w200" maxlength="6" type="text" name="value" value="%s" /><br />
    <span class="adminlabel">Tag comment</span>
    <input class="admin_w200" type="text" name="name" value="%s" /><br />
    """ % ((name=='' and value[0] or name), value[0])
    text += """Or existing tag:<br />
    <span class="adminlabel">Tag</span>
    <select name="value" class="admin_w200">
    <option value="-1">- Select a tag -</option>
    """

    fld_tags = get_fld_tags(fldID)
    tags = get_tags()
    fld_tags = dict(map(lambda x: (x[1], x[0]), fld_tags))

    for (id_tag, tname, tvalue) in tags:
        if not fld_tags.has_key(id_tag):
            text += """<option value="%s" %s>%s</option>""" % (tvalue, (tvalue==value[1] and 'selected="selected"' or ''), "%s - %s" % (tvalue, tname))
    text += """</select>"""

    output = createhiddenform(action="%s/admin/bibindex/bibindexadmin.py/addtag" % CFG_SITE_URL,
                              text=text,
                              fldID=fldID,
                              ln=ln,
                              button="Add tag",
                              confirm=1)

    if (value[0] and value[1] in [-1, "-1"]) or (not value[0] and value[1] not in [-1, "-1"]):
        if confirm in ["1", 1]:
            res = add_fld_tag(fldID, name, (value[0] !='' and value[0] or value[1]))
            output += write_outcome(res)
    elif confirm not in ["-1", -1]:
        output += """<b><span class="info">Please choose to add either a new or an existing MARC tag, but not both.</span></b>
        """

    body = [output]

    if callback:
        return perform_modifyfieldtags(fldID, ln, "perform_addtag", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_modifytag(fldID, tagID, ln=CFG_SITE_LANG, name='', value='', callback='yes', confirm=-1):
    """form to modify a field.
    fldID - the field to change."""

    subtitle  = ""
    output  = ""

    fld_dict = dict(get_def_name('', "field"))

    fldID = int(fldID)
    tagID = int(tagID)
    tag = get_tags(tagID)
    if confirm in [-1, "-1"] and not value and not name:
        name = tag[0][1]
        value = tag[0][2]

    subtitle = """<a name="3.1"></a>Modify MARC tag"""

    text = """
    Any modifications will apply to all logical fields using this tag.<br />
    <span class="adminlabel">Tag value</span>
    <input class="admin_w200" type="text" name="value" value="%s" /><br />
    <span class="adminlabel">Comment</span>
    <input class="admin_w200" type="text" name="name" value="%s" /><br />
    """ % (value, name)

    output += createhiddenform(action="modifytag#4.1",
                               text=text,
                               button="Modify",
                               fldID=fldID,
                               tagID=tagID,
                               ln=ln,
                               confirm=1)

    if name and value and confirm in [1, "1"]:
        res = modify_tag(tagID, name, value)
        output += write_outcome(res)

    body = [output]

    if callback:
        return perform_modifyfieldtags(fldID, ln, "perform_modifytag", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_removefieldtag(fldID, tagID, ln=CFG_SITE_LANG, callback='yes', confirm=0):
    """form to remove a tag from a field.
    fldID - the current field, remove the tag from this field.
    tagID - remove the tag with this id"""

    subtitle = """<a name="4.1"></a>Remove MARC tag from logical field"""
    output  = ""

    fld_dict = dict(get_def_name('', "field"))

    if fldID and tagID:
        fldID = int(fldID)
        tagID = int(tagID)
        tag = get_fld_tags(fldID, tagID)
        if confirm not in ["1", 1]:
            text = """Do you want to remove the tag '%s - %s ' from the field '%s'.""" % (tag[0][3], tag[0][2], fld_dict[fldID])
            output += createhiddenform(action="removefieldtag#4.1",
                                       text=text,
                                       button="Confirm",
                                       fldID=fldID,
                                       tagID=tagID,
                                       confirm=1)
        elif confirm in ["1", 1]:
            res = remove_fldtag(fldID, tagID)
            output += write_outcome(res)

    body = [output]

    if callback:
        return perform_modifyfieldtags(fldID, ln, "perform_removefieldtag", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_addindexfield(idxID, ln=CFG_SITE_LANG, fldID='', callback="yes", confirm=-1):
    """form to add a new field.
    fldNAME - the name of the new field
    code - the field code"""

    output = ""
    subtitle = """<a name="4.1"></a>Add logical field to index"""
    text = """
    <span class="adminlabel">Field name</span>
    <select name="fldID" class="admin_w200">
    <option value="-1">- Select a field -</option>
    """

    fld = get_fld()

    for (fldID2, fldNAME, fldCODE) in fld:
        text += """<option value="%s" %s>%s</option>""" % (fldID2, (fldID==fldID2 and 'selected="selected"' or ''), fldNAME)
    text += """</select>"""

    output = createhiddenform(action="%s/admin/bibindex/bibindexadmin.py/addindexfield" % CFG_SITE_URL,
                              text=text,
                              idxID=idxID,
                              ln=ln,
                              button="Add field",
                              confirm=1)

    if fldID and not fldID in [-1, "-1"] and confirm in ["1", 1]:
        res = add_idx_fld(idxID, fldID)
        output += write_outcome(res)
    elif confirm in ["1", 1]:
        output += """<b><span class="info">Please select a field to add.</span></b>"""

    body = [output]

    if callback:
        return perform_modifyindexfields(idxID, ln, "perform_addindexfield", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_removeindexfield(idxID, fldID, ln=CFG_SITE_LANG, callback='yes', confirm=0):
    """form to remove a field from an index.
    idxID - the current index, remove the field from this index.
    fldID - remove the field with this id"""

    subtitle = """<a name="3.1"></a>Remove field from index"""
    output  = ""

    if fldID and idxID:
        fldID = int(fldID)
        idxID = int(idxID)
        fld = get_fld(fldID)
        idx = get_idx(idxID)
        if fld and idx and confirm not in ["1", 1]:
            text = """Do you want to remove the field '%s' from the index '%s'.""" % (fld[0][1], idx[0][1])
            output += createhiddenform(action="removeindexfield#3.1",
                                       text=text,
                                       button="Confirm",
                                       idxID=idxID,
                                       fldID=fldID,
                                       confirm=1)
        elif confirm in ["1", 1]:
            res = remove_idxfld(idxID, fldID)
            output += write_outcome(res)

    body = [output]

    if callback:
        return perform_modifyindexfields(idxID, ln, "perform_removeindexfield", addadminbox(subtitle, body))
    else:
        return addadminbox(subtitle, body)

def perform_switchtagscore(fldID, id_1, id_2, ln=CFG_SITE_LANG):
    """Switch the score of id_1 and id_2 in the table type.
    colID - the current collection
    id_1/id_2 - the id's to change the score for.
    type - like "format" """

    output = ""
    name_1 = run_sql("select name from tag where id=%s", (id_1, ))[0][0]
    name_2 = run_sql("select name from tag where id=%s", (id_2, ))[0][0]
    res = switch_score(fldID, id_1, id_2)
    output += write_outcome(res)
    return perform_modifyfieldtags(fldID, ln, content=output)

def perform_deletetag(fldID, ln=CFG_SITE_LANG, tagID=-1, callback='yes', confirm=-1):
    """form to delete an MARC tag not in use.
    fldID - the collection id of the current collection.
    fmtID - the format id to delete."""

    subtitle = """<a name="10.3"></a>Delete an unused MARC tag"""
    output  = """
    <dl>
     <dd>Deleting an MARC tag will also delete the translations associated.</dd>
    </dl>
    """

    fldID = int(fldID)
    if tagID not in [-1," -1"] and confirm in [1, "1"]:
        ares = delete_tag(tagID)

    fld_tag = get_fld_tags()
    fld_tag = dict(map(lambda x: (x[1], x[0]), fld_tag))

    tags = get_tags()
    text  = """
    <span class="adminlabel">MARC tag</span>
    <select name="tagID" class="admin_w200">
    """
    text += """<option value="-1">- Select MARC tag -"""
    i = 0
    for (id, name, value) in tags:
        if not fld_tag.has_key(id):
            text += """<option value="%s" %s>%s</option>""" % (id, id  == int(tagID) and 'selected="selected"' or '', "%s - %s" % (value, name))
            i += 1

    text += """</select><br />"""

    if i == 0:
        output += """<b><span class="info">No unused MARC tags</span></b><br />"""
    else:
        output += createhiddenform(action="deletetag#4.1",
                                   text=text,
                                   button="Delete",
                                   fldID=fldID,
                                   ln=ln,
                                   confirm=0)

    if tagID not in [-1,"-1"]:
        tagID = int(tagID)
        tags = get_tags(tagID)
        if confirm in [0, "0"]:
            text = """<b>Do you want to delete the MARC tag '%s'.</b>""" % tags[0][2]
            output += createhiddenform(action="deletetag#4.1",
                                       text=text,
                                       button="Confirm",
                                       fldID=fldID,
                                       tagID=tagID,
                                       ln=ln,
                                       confirm=1)

        elif confirm in [1, "1"]:
            output += write_outcome(ares)
    elif confirm not in [-1, "-1"]:
        output  += """<b><span class="info">Choose a MARC tag to delete.</span></b>"""

    body = [output]

    output = "<br />" + addadminbox(subtitle, body)
    return perform_modifyfieldtags(fldID, ln, content=output)

def compare_on_val(first, second):
    """Compare the two values"""

    return cmp(first[1], second[1])

def get_col_fld(colID=-1, type = '', id_field=''):
    """Returns either all portalboxes associated with a collection, or based on either colID or language or both.
    colID - collection id
    ln - language id"""

    sql = "SELECT id_collection,id_field,id_fieldvalue,type,score,score_fieldvalue FROM collection_field_fieldvalue, field WHERE id_field=field.id"

    params = []
    try:
        if id_field:
            sql += " AND id_field=%s"
            params.append(id_field)
        sql += " ORDER BY type, score desc, score_fieldvalue desc"
        res = run_sql(sql, tuple(params))
        return res
    except StandardError, e:
        return ""

def get_idx(idxID=''):
    sql = "SELECT id,name,description,last_updated,stemming_language FROM idxINDEX"
    params = []
    try:
        if idxID:
            sql += " WHERE id=%s"
            params.append(idxID)
        sql += " ORDER BY id asc"
        res = run_sql(sql, tuple(params))
        return res
    except StandardError, e:
        return ""

def get_fld_tags(fldID='', tagID=''):
    """Returns tags associated with a field.
    fldID - field id
    tagID - tag id"""

    sql = "SELECT id_field,id_tag, tag.name, tag.value, score FROM field_tag,tag  WHERE tag.id=field_tag.id_tag"
    params = []

    try:
        if fldID:
            sql += " AND id_field=%s"
            params.append(fldID)
        if tagID:
            sql += " AND id_tag=%s"
            params.append(tagID)
        sql += " ORDER BY score desc, tag.value, tag.name"
        res = run_sql(sql, tuple(params))
        return res
    except StandardError, e:
        return ""

def get_tags(tagID=''):
    """Returns all or a given tag.
    tagID - tag id
    ln - language id"""

    sql = "SELECT id, name, value FROM tag"
    params = []

    try:
        if tagID:
            sql += " WHERE id=%s"
            params.append(tagID)
        sql += " ORDER BY name, value"
        res = run_sql(sql, tuple(params))
        return res
    except StandardError, e:
        return ""

def get_fld(fldID=''):
    """Returns all fields or only the given field"""

    try:
        if not fldID:
            res = run_sql("SELECT id, name, code FROM field ORDER by name, code")
        else:
            res = run_sql("SELECT id, name, code FROM field WHERE id=%s ORDER by name, code", (fldID, ))
        return res
    except StandardError, e:
        return ""

def get_fld_value(fldvID = ''):
    """Returns fieldvalue"""

    try:
        sql = "SELECT id, name, value FROM fieldvalue"
        params = []
        if fldvID:
            sql += " WHERE id=%s"
            params.append(fldvID)
        res = run_sql(sql, tuple(params))
        return res
    except StandardError, e:
        return ""

def get_idx_fld(idxID=''):
    """Return a list of fields associated with one or all indexes"""
    try:
        sql = "SELECT id_idxINDEX, idxINDEX.name, id_field, field.name, regexp_punctuation, regexp_alphanumeric_separators FROM idxINDEX, field, idxINDEX_field WHERE idxINDEX.id = idxINDEX_field.id_idxINDEX AND field.id = idxINDEX_field.id_field"
        params = []
        if idxID:
            sql += " AND id_idxINDEX=%s"
            params.append(idxID)
        sql += " ORDER BY id_idxINDEX asc"
        res = run_sql(sql, tuple(params))
        return res
    except StandardError, e:
        return ""

def get_col_nametypes():
    """Return a list of the various translationnames for the fields"""

    type = []
    type.append(('ln', 'Long name'))
    return type

def get_fld_nametypes():
    """Return a list of the various translationnames for the fields"""

    type = []
    type.append(('ln', 'Long name'))
    return type

def get_idx_nametypes():
    """Return a list of the various translationnames for the index"""

    type = []
    type.append(('ln', 'Long name'))
    return type

def get_sort_nametypes():
    """Return a list of the various translationnames for the fields"""

    type = {}
    type['soo'] = 'Sort options'
    type['seo'] = 'Search options'
    type['sew'] = 'Search within'
    return type

def remove_fld(colID,fldID, fldvID=''):
    """Removes a field from the collection given.
    colID - the collection the format is connected to
    fldID - the field which should be removed from the collection."""

    try:
        sql = "DELETE FROM collection_field_fieldvalue WHERE id_collection=%s AND id_field=%s"
        params = [colID, fldID]
        if fldvID:
            sql += " AND id_fieldvalue=%s"
            params.append(fldvID)
        res = run_sql(sql, tuple(params))
        return (1, "")
    except StandardError, e:
        return (0, e)

def remove_idxfld(idxID, fldID):
    """Remove a field from a index in table idxINDEX_field
    idxID - index id from idxINDEX
    fldID - field id from field table"""

    try:
        sql = "DELETE FROM idxINDEX_field WHERE id_field=%s and id_idxINDEX=%s"
        res = run_sql(sql, (fldID, idxID))
        return (1, "")
    except StandardError, e:
        return (0, e)

def remove_fldtag(fldID,tagID):
    """Removes a tag from the field given.
    fldID - the field the tag is connected to
    tagID - the tag which should be removed from the field."""

    try:
        sql = "DELETE FROM field_tag WHERE id_field=%s AND id_tag=%s"
        res = run_sql(sql, (fldID, tagID))
        return (1, "")
    except StandardError, e:
        return (0, e)

def delete_tag(tagID):
    """Deletes all data for the given field
    fldID - delete all data in the tables associated with field and this id """

    try:
        res = run_sql("DELETE FROM tag where id=%s", (tagID, ))
        return (1, "")
    except StandardError, e:
        return (0, e)

def delete_idx(idxID):
    """Deletes all data for the given index together with the idxWORDXXR and idxWORDXXF tables"""
    try:
        idxID = int(idxID)
        res = run_sql("DELETE FROM idxINDEX WHERE id=%s", (idxID, ))
        res = run_sql("DELETE FROM idxINDEXNAME WHERE id_idxINDEX=%s", (idxID, ))
        res = run_sql("DELETE FROM idxINDEX_field WHERE id_idxINDEX=%s", (idxID, ))
        res = run_sql("DROP TABLE idxWORD%02dF" % idxID) # kwalitee: disable=sql
        res = run_sql("DROP TABLE idxWORD%02dR" % idxID) # kwalitee: disable=sql
        res = run_sql("DROP TABLE idxPAIR%02dF" % idxID) # kwalitee: disable=sql
        res = run_sql("DROP TABLE idxPAIR%02dR" % idxID) # kwalitee: disable=sql
        res = run_sql("DROP TABLE idxPHRASE%02dF" % idxID) # kwalitee: disable=sql
        res = run_sql("DROP TABLE idxPHRASE%02dR" % idxID) # kwalitee: disable=sql
        return (1, "")
    except StandardError, e:
        return (0, e)


def delete_fld(fldID):
    """Deletes all data for the given field
    fldID - delete all data in the tables associated with field and this id """

    try:
        res = run_sql("DELETE FROM collection_field_fieldvalue WHERE id_field=%s", (fldID, ))
        res = run_sql("DELETE FROM field_tag WHERE id_field=%s", (fldID, ))
        res = run_sql("DELETE FROM idxINDEX_field WHERE id_field=%s", (fldID, ))
        res = run_sql("DELETE FROM field WHERE id=%s", (fldID, ))
        return (1, "")
    except StandardError, e:
        return (0, e)

def add_idx(idxNAME):
    """Add a new index. returns the id of the new index.
    idxID - the id for the index, number
    idxNAME - the default name for the default language of the format."""

    try:
        idxID = 0
        res = run_sql("SELECT id from idxINDEX WHERE name=%s", (idxNAME,))
        if res:
            return (0, (0, "A index with the given name already exists."))

        for i in xrange(1, 100):
            res = run_sql("SELECT id from idxINDEX WHERE id=%s", (i, ))
            res2 = get_table_status_info("idxWORD%02d%%" % i)
            if not res and not res2:
                idxID = i
                break
        if idxID == 0:
            return (0, (0, "Not possible to create new indexes, delete an index and try again."))

        res = run_sql("INSERT INTO idxINDEX (id, name) VALUES (%s,%s)", (idxID, idxNAME))
        type = get_idx_nametypes()[0][0]
        res = run_sql("INSERT INTO idxINDEXNAME (id_idxINDEX, ln, type, value) VALUES (%s,%s,%s,%s)",
                      (idxID, CFG_SITE_LANG, type, idxNAME))

        res = run_sql("""CREATE TABLE IF NOT EXISTS idxWORD%02dF (
                            id mediumint(9) unsigned NOT NULL auto_increment,
                            term varchar(50) default NULL,
                            hitlist longblob,
                            PRIMARY KEY  (id),
                            UNIQUE KEY term (term)
                            ) ENGINE=MyISAM""" % idxID)

        res = run_sql("""CREATE TABLE IF NOT EXISTS idxWORD%02dR (
                            id_bibrec mediumint(9) unsigned NOT NULL,
                            termlist longblob,
                            type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                            PRIMARY KEY (id_bibrec,type)
                            ) ENGINE=MyISAM""" % idxID)

        res = run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR%02dF (
                            id mediumint(9) unsigned NOT NULL auto_increment,
                            term varchar(100) default NULL,
                            hitlist longblob,
                            PRIMARY KEY  (id),
                            UNIQUE KEY term (term)
                            ) ENGINE=MyISAM""" % idxID)

        res = run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR%02dR (
                            id_bibrec mediumint(9) unsigned NOT NULL,
                            termlist longblob,
                            type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                            PRIMARY KEY (id_bibrec,type)
                            ) ENGINE=MyISAM""" % idxID)

        res = run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE%02dF (
                            id mediumint(9) unsigned NOT NULL auto_increment,
                            term text default NULL,
                            hitlist longblob,
                            PRIMARY KEY  (id),
                            KEY term (term(50))
                            ) ENGINE=MyISAM""" % idxID)

        res = run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE%02dR (
                            id_bibrec mediumint(9) unsigned NOT NULL default '0',
                            termlist longblob,
                            type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                            PRIMARY KEY  (id_bibrec,type)
                            ) ENGINE=MyISAM""" % idxID)

        res = run_sql("SELECT id from idxINDEX WHERE id=%s", (idxID, ))
        res2 = get_table_status_info("idxWORD%02dF" % idxID)
        res3 = get_table_status_info("idxWORD%02dR" % idxID)
        if res and res2 and res3:
            return (1, res[0][0])
        elif not res:
            return (0, (0, "Could not add the new index to idxINDEX"))
        elif not res2:
            return (0, (0, "Forward table not created for unknown reason."))
        elif not res3:
            return (0, (0, "Reverse table not created for unknown reason."))
    except StandardError, e:
        return (0, e)

def add_fld(name, code):
    """Add a new logical field. Returns the id of the field.
    code - the code for the field,
    name - the default name for the default language of the field."""

    try:
        type = get_fld_nametypes()[0][0]
        res = run_sql("INSERT INTO field (name, code) VALUES (%s,%s)", (name, code))
        fldID = run_sql("SELECT id FROM field WHERE code=%s", (code,))
        res = run_sql("INSERT INTO fieldname (id_field, type, ln, value) VALUES (%s,%s,%s,%s)", (fldID[0][0], type, CFG_SITE_LANG, name))
        if fldID:
            return (1, fldID[0][0])
        else:
            raise StandardError
    except StandardError, e:
        return (0, e)

def add_fld_tag(fldID, name, value):
    """Add a sort/search/field to the collection.
    colID - the id of the collection involved
    fmtID - the id of the format.
    score - the score of the format, decides sorting, if not given, place the format on top"""

    try:
        res = run_sql("SELECT score FROM field_tag WHERE id_field=%s ORDER BY score desc", (fldID, ))
        if res:
            score = int(res[0][0]) + 1
        else:
            score = 0
        res = run_sql("SELECT id FROM tag WHERE value=%s", (value,))
        if not res:
            if name == '':
                name = value
            res = run_sql("INSERT INTO tag (name, value) VALUES (%s,%s)", (name,  value))
            res = run_sql("SELECT id FROM tag WHERE value=%s", (value,))

        res = run_sql("INSERT INTO field_tag(id_field, id_tag, score) values(%s, %s, %s)",  (fldID, res[0][0], score))
        return (1, "")
    except StandardError, e:
        return (0, e)

def add_idx_fld(idxID, fldID):
    """Add a field to an index"""

    try:
        sql = "SELECT id_idxINDEX FROM idxINDEX_field WHERE id_idxINDEX=%s and id_field=%s"
        res = run_sql(sql, (idxID, fldID))
        if res:
            return (0, (0, "The field selected already exists for this index"))
        sql = "INSERT INTO idxINDEX_field(id_idxINDEX, id_field) values (%s, %s)"
        res = run_sql(sql,  (idxID, fldID))
        return (1, "")
    except StandardError, e:
        return (0, e)

def modify_idx(idxID, idxNAME, idxDESC):
    """Modify index name or index description in idxINDEX table"""

    try:
        res = run_sql("UPDATE idxINDEX SET name=%s WHERE id=%s", (idxNAME, idxID))
        res = run_sql("UPDATE idxINDEX SET description=%s WHERE ID=%s", (idxDESC, idxID))
        return (1, "")
    except StandardError, e:
        return (0, e)

def modify_idx_stemming(idxID, idxSTEM):
    """Modify the index stemming language in idxINDEX table"""

    try:
        res = run_sql("UPDATE idxINDEX SET stemming_language=%s WHERE ID=%s", (idxSTEM, idxID))
        return (1, "")
    except StandardError, e:
        return (0, e)


def modify_fld(fldID, code):
    """Modify the code of field
    fldID - the id of the field to modify
    code - the new code"""

    try:
        sql = "UPDATE field SET code=%s"
        sql += " WHERE id=%s"
        res = run_sql(sql, (code, fldID))
        return (1, "")
    except StandardError, e:
        return (0, e)

def modify_tag(tagID, name, value):
    """Modify the name and value of a tag.
    tagID - the id of the tag to modify
    name - the new name of the tag
    value - the new value of the tag"""

    try:
        sql = "UPDATE tag SET name=%s WHERE id=%s"
        res = run_sql(sql, (name, tagID))
        sql = "UPDATE tag SET value=%s WHERE id=%s"
        res = run_sql(sql, (value, tagID))
        return (1, "")
    except StandardError, e:
        return (0, e)

def switch_score(fldID, id_1, id_2):
    """Switch the scores of id_1 and id_2 in the table given by the argument.
    colID - collection the id_1 or id_2 is connected to
    id_1/id_2 - id field from tables like format..portalbox...
    table - name of the table"""
    try:
        res1 = run_sql("SELECT score FROM field_tag WHERE id_field=%s and id_tag=%s", (fldID, id_1))
        res2 = run_sql("SELECT score FROM field_tag WHERE id_field=%s and id_tag=%s", (fldID, id_2))
        res = run_sql("UPDATE field_tag SET score=%s WHERE id_field=%s and id_tag=%s", (res2[0][0], fldID, id_1))
        res = run_sql("UPDATE field_tag SET score=%s WHERE id_field=%s and id_tag=%s", (res1[0][0], fldID, id_2))
        return (1, "")
    except StandardError, e:
        return (0, e)

def get_lang_list(table, field, id):
    langs = run_sql("SELECT ln FROM %s WHERE %s=%%s" % (wash_table_column_name(table), wash_table_column_name(field)), (id, )) # kwalitee: disable=sql
    exists = {}
    lang = ''
    for lng in langs:
        if not exists.has_key(lng[0]):
            lang += lng[0] + ", "
        exists[lng[0]] = 1
    if lang.endswith(", "):
        lang = lang [:-2]
    if len(exists) == 0:
        lang = """<b><span class="info">None</span></b>"""
    return lang

def check_user(req, role, adminarea=2, authorized=0):
    # FIXME: Add doctype.
    # This function is similar to the one found in
    # bibharvest/lib/oai_repository_admin.py, bibrank/lib/bibrankadminlib.py and
    # websubmit/lib/websubmitadmin_engine.py.
    auth_code, auth_message = acc_authorize_action(req, role)
    if not authorized and auth_code != 0:
        return ("false", auth_message)
    return ("", auth_message)
