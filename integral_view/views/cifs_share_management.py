
import django, django.template

import os
import integral_view

from integral_view.forms import samba_shares_forms

from integralstor_common import audit, networking,zfs, acl
from integralstor_common import cifs as cifs_common
from integralstor_unicell import cifs as cifs_unicell
from integralstor_unicell import local_users

def view_cifs_shares(request):

  return_dict = {}
  try:
    template = 'logged_in_error.html'
    shares_list, err = cifs_common.load_shares_list()
    if err:
      raise Exception(err)
  
    if not "error" in return_dict:
      if "ack" in request.GET:
        if request.GET["ack"] == "saved":
          return_dict['ack_message'] = "Share information successfully updated"
        elif request.GET["ack"] == "created":
          return_dict['ack_message'] = "Share successfully created"
        elif request.GET["ack"] == "deleted":
          return_dict['ack_message'] = "Share successfully deleted"
      return_dict["shares_list"] = shares_list
      template = "view_cifs_shares.html"
    return django.shortcuts.render_to_response(template, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "shares_base.html"
    return_dict["page_title"] = 'CIFS shares'
    return_dict['tab'] = 'view_cifs_shares_tab'
    return_dict["error"] = 'Error loading CIFS share list'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))



def view_cifs_share(request):

  return_dict = {}
  try:
    template = 'logged_in_error.html'
  
    if not "error" in return_dict:
      if "ack" in request.GET:
        if request.GET["ack"] == "ace_deleted":
          return_dict['ack_message'] = "ACL entry successfully removed"
        elif request.GET["ack"] == "aces_added":
          return_dict['ack_message'] = "ACL entries successfully added"
        elif request.GET["ack"] == "aces_modified":
          return_dict['ack_message'] = "ACL entries successfully modified"

    if request.method != "GET":
      raise Exception("Incorrect access method. Please use the menus")
  
    if "index" not in request.GET or "access_mode" not in request.GET:
      raise Exception("Insufficient parameters. Please use the menus")
  
    access_mode = request.GET["access_mode"]
    index = request.GET["index"]
  
    if "ack" in request.GET and request.GET["ack"] == "saved":
      return_dict["ack_message"] = "Information updated successfully"
  
    valid_users_list = None
    share, err = cifs_common.load_share_info(access_mode, index)
    if err:
      raise Exception(err)
    if not share:
      raise Exception('Specified share not found')

    '''
    valid_users_list, err = cifs_common.load_valid_users_list(share["share_id"])
    if err:
      raise Exception(err)
    print valid_users_list
    if valid_users_list:
        return_dict["valid_users_list"] = valid_users_list
    '''

    aces, err = acl.get_all_aces(share['path'])
    if err:
      raise Exception(err)
    minimal_aces, err = acl.get_minimal_aces(aces)
    if err:
      raise Exception(err)
    user_aces, err = acl.get_ug_aces(aces, None, 'user')
    if err:
      raise Exception(err)
    group_aces, err = acl.get_ug_aces(aces, None, 'group')
    if err:
      raise Exception(err)

    return_dict['aces'] = aces
    return_dict['minimal_aces'] = minimal_aces
    if user_aces:
      return_dict['user_aces'] = user_aces
    if group_aces:
      return_dict['group_aces'] = group_aces
    return_dict["share"] = share
    template = 'view_cifs_share.html'
  
    return django.shortcuts.render_to_response(template, return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "shares_base.html"
    return_dict["page_title"] = 'CIFS share details'
    return_dict['tab'] = 'view_cifs_shares_tab'
    return_dict["error"] = 'Error loading CIFS share details'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

def edit_cifs_share(request):

  return_dict = {}
  try:
    user_list, err = cifs_unicell.get_user_list()
    if err:
      raise Exception(err)
    group_list, err = cifs_unicell.get_group_list()
    if err:
      raise Exception(err)

    if request.method == "GET":
      # Shd be an edit request
      if "share_id" not in request.GET:
        raise Exception("Unknown share specified")

      share_id = request.GET["share_id"]
      share_dict, err = cifs_common.load_share_info("by_id", share_id)
      if err:
        raise Exception(err)
      '''
      valid_users_list, err = cifs_common.load_valid_users_list(share_dict["share_id"])
      if err:
        raise Exception(err)
      '''
  
      # Set initial form values
      initial = {}
      initial["share_id"] = share_dict["share_id"]
      initial["name"] = share_dict["name"]
      initial["path"] = share_dict["path"]
      if share_dict["guest_ok"]:
        initial["guest_ok"] = True
      else:
        initial["guest_ok"] = False
      if share_dict["browseable"]:
        initial["browseable"] = True
      else:
        initial["browseable"] = False
      '''
      if share_dict["read_only"]:
        initial["read_only"] = True
      else:
        initial["read_only"] = False
      '''
      initial["comment"] = share_dict["comment"]
  
      '''
      if valid_users_list:
        vgl = []
        vul = []
        for u in valid_users_list:
          if u["grp"]:
            vgl.append(u["name"])
          else:
            vul.append(u["name"])
        initial["users"] = vul
        initial["groups"] = vgl
      '''
  
      #form = samba_shares_forms.EditShareForm(initial = initial, user_list = user_list, group_list = group_list)
      form = samba_shares_forms.EditShareForm(initial = initial)
  
      return_dict["form"] = form
      return django.shortcuts.render_to_response('edit_cifs_share.html', return_dict, context_instance=django.template.context.RequestContext(request))
  
    else:
  
      # Shd be an save request
      #form = samba_shares_forms.EditShareForm(request.POST, user_list = user_list, group_list = group_list)
      form = samba_shares_forms.EditShareForm(request.POST)
      return_dict["form"] = form
      if form.is_valid():
        cd = form.cleaned_data
        name = cd["name"]
        share_id = cd["share_id"]
        path = cd["path"]
        if "comment" in cd:
          comment = cd["comment"]
        else:
          comment = None
        if "read_only" in cd:
          read_only = cd["read_only"]
        else:
          read_only = False
        if "browseable" in cd:
          browseable = cd["browseable"]
        else:
          browseable = False
        '''
        if "guest_ok" in cd:
          guest_ok = cd["guest_ok"]
        else:
          guest_ok = False
        if "users" in cd:
          users = cd["users"]
        else:
          users = None
        if "groups" in cd:
          groups = cd["groups"]
        else:
          groups = None
        '''
        #logger.debug("Save share request, name %s path %s, comment %s, read_only %s, browseable %s, guest_ok %s, users %s, groups %s, vol %s"%(name, path, comment, read_only, browseable, guest_ok, users, groups))
        ret, err = cifs_common.save_share(share_id, name, comment, False, read_only, path, browseable, None, None)
        if err:
          raise Exception(err)
        ret, err = cifs_unicell.generate_smb_conf()
        if err:
          raise Exception(err)
  
        audit_str = "Modified share %s"%cd["name"]
        audit.audit("modify_cifs_share", audit_str, request.META)
  
        return django.http.HttpResponseRedirect('/view_cifs_share?access_mode=by_id&index=%s&ack=saved'%cd["share_id"])
  
      else:
        #Invalid form
        return django.shortcuts.render_to_response('edit_cifs_share.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "shares_base.html"
    return_dict["page_title"] = 'Modify a CIFS share'
    return_dict['tab'] = 'view_cifs_shares_tab'
    return_dict["error"] = 'Error modifying CIFS share'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


  
def delete_cifs_share(request):
  
  return_dict = {}
  try:
    if request.method == "GET":
      #Return the conf page
      share_id = request.GET["share_id"]
      name = request.GET["name"]
      return_dict["share_id"] = share_id
      return_dict["name"] = name
      return django.shortcuts.render_to_response("delete_cifs_share_conf.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      share_id = request.POST["share_id"]
      name = request.POST["name"]
      #logger.debug("Delete share request for name %s"%name)
      ret, err = cifs_common.delete_share(share_id)
      if err:
        raise Exception(err)
      ret, err = cifs_unicell.generate_smb_conf()
      if err:
        raise Exception(err)
  
      audit_str = "Deleted CIFS share %s"%name
      audit.audit("delete_cifs_share", audit_str, request.META)
      return django.http.HttpResponseRedirect('/view_cifs_shares?ack=deleted')
  except Exception, e:
    return_dict['base_template'] = "shares_base.html"
    return_dict["page_title"] = 'Delete a CIFS share'
    return_dict['tab'] = 'view_cifs_shares_tab'
    return_dict["error"] = 'Error deleting a  CIFS share'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def create_cifs_share(request):

  return_dict = {}
  try:

    pools, err = zfs.get_pools()
    if err:
      raise Exception('No ZFS pools available. Please create a pool and dataset before creating shares.')

    ds_list = [] 
    for pool in pools:
      for ds in pool["datasets"]:
        if ds['properties']['type']['value'] == 'filesystem':
          ds_list.append((ds['properties']['mountpoint']['value'], ds["name"]))

    if not ds_list:
      raise Exception('No ZFS datasets available. Please create a dataset before creating shares.')
  
    if 'dataset' in request.REQUEST:
      dataset = request.REQUEST['dataset']
    else:
      dataset = ds_list[0][0]

    if 'path' in request.REQUEST:
      path = request.REQUEST['path']
    else:
      path = dataset

    return_dict['path'] = path
    return_dict["dataset"] = ds_list

    initial = {}
    initial['path'] = path
    initial['dataset'] = dataset
    if request.method == "GET":
      #Return the form
      initial['guest_ok'] = True
      if 'name' in request.GET:
        initial['name'] = request.GET['name']

      #form = samba_shares_forms.CreateShareForm(user_list = user_list, group_list = group_list, dataset_list = ds_list, initial = {'guest_ok': True})
      form = samba_shares_forms.CreateShareForm(dataset_list = ds_list, initial = initial)
      return_dict["form"] = form

      return django.shortcuts.render_to_response("create_cifs_share.html", return_dict, context_instance = django.template.context.RequestContext(request))
    else:
      #Form submission so create
      return_dict = {}
      #form = samba_shares_forms.CreateShareForm(request.POST, user_list = user_list, group_list = group_list, dataset_list = ds_list)
      form = samba_shares_forms.CreateShareForm(request.POST, initial = initial, dataset_list = ds_list)
      return_dict["form"] = form
      if form.is_valid():
        cd = form.cleaned_data
        print cd
        name = cd["name"]
        path = cd["path"]
        if not path:
          return_dict["path_error"] = "Please select a dataset."
          return django.shortcuts.render_to_response("create_cifs_share.html", return_dict, context_instance = django.template.context.RequestContext(request))
        if 'new_folder' in cd and cd['new_folder']:
          try:
            path = '%s/%s'%(cd['path'], cd['new_folder'])
            #print path
            os.mkdir(path)
            audit_str = 'Created new directory "%s" in "%s"'%(cd['new_folder'], cd['path'])
            audit.audit("create_dir", audit_str, request.META)
          except Exception, e:
            raise Exception('Error creating subfolder %s : %s'%(cd['new_folder'], str(e)))
        os.chown(path,1000,1000)

        if "comment" in cd:
          comment = cd["comment"]
        else:
          comment = None
        if "read_only" in cd:
          read_only = cd["read_only"]
        else:
          read_only = None
        if "browseable" in cd:
          browseable = cd["browseable"]
        else:
          browseable = None

        '''
        if "guest_ok" in cd:
          guest_ok = cd["guest_ok"]
        else:
          guest_ok = None
        if "users" in cd:
          users = cd["users"]
        else:
          users = None
        if "groups" in cd:
          groups = cd["groups"]
        else:
          groups = None
        '''

        guest_ok = True
        #logger.debug("Create share request, name %s path %s, comment %s, read_only %s, browseable %s, guest_ok %s, users %s, groups %s, vol %s"%(name, path, comment, read_only, browseable, guest_ok, users, groups))
        #print '1'
        ret, err = cifs_common.create_share(name, comment, True, read_only, path, path, browseable, None, None, "unicell_novol")
        #print '2'
        if err:
          raise Exception(err)
        ret, err = cifs_unicell.generate_smb_conf()
        #print '3'
        if err:
          raise Exception(err)
  
        audit_str = "Created Samba share %s"%name
        audit.audit("create_cifs_share", audit_str, request.META)
        return django.http.HttpResponseRedirect('/view_cifs_shares?ack=created')
      else:
        return django.shortcuts.render_to_response("create_cifs_share.html", return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "shares_base.html"
    return_dict["page_title"] = 'Create a CIFS share'
    return_dict['tab'] = 'view_cifs_shares_tab'
    return_dict["error"] = 'Error creating a CIFS share'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def samba_server_settings(request):

  return_dict = {}
  #print 'a1'
  try:
    d, err = cifs_common.load_auth_settings()
    if err:
      raise Exception(err)
  
    if "action" in request.REQUEST and request.REQUEST["action"] == "edit":
      ini = {}
      if d:    
        for k in d.keys():
          if d[k]:
            ini[k] = d[k] 
      if d and d["security"] == "ads":
        form = samba_shares_forms.AuthADSettingsForm(initial=ini)
      #elif d["security"] == "users":
      else:
        #print 'c'
        form = samba_shares_forms.AuthUsersSettingsForm(initial=ini)
        #print 'd'
      return_dict["form"] = form
      return django.shortcuts.render_to_response('edit_samba_server_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
  
    # Else a view request
    return_dict["samba_global_dict"] = d
    #print 'a2'
  
    if "ack" in request.REQUEST and request.REQUEST["ack"] == "saved":
      return_dict["ack_message"] = "Information updated successfully"
    return django.shortcuts.render_to_response('view_samba_server_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "services_base.html"
    return_dict["page_title"] = 'Modify CIFS authentication settings'
    return_dict['tab'] = 'auth_server_settings_tab'
    return_dict["error"] = 'Error modifying CIFS authentication settings'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))


def edit_auth_method(request):
  return_dict = {}
  try:
    d, err = cifs_common.load_auth_settings()
    if err:
      raise Exception(err)
    return_dict["samba_global_dict"] = d
  
    if request.method == "GET":
      return django.shortcuts.render_to_response('edit_auth_method.html', return_dict, context_instance=django.template.context.RequestContext(request))
    else:
      #Save request
      if "auth_method" not in request.POST:
        return_dict["error"] = "Please select an authentication method" 
        return django.shortcuts.render_to_response('edit_auth_method.html', return_dict, context_instance=django.template.context.RequestContext(request))
      security = request.POST["auth_method"]
      if security == d["security"]:
        return_dict["error"] = "Selected authentication method is the same as before." 
        return django.shortcuts.render_to_response('edit_auth_method.html', return_dict, context_instance=django.template.context.RequestContext(request))
  
      ret, err = cifs_common.change_auth_method(security)
      if err:
        raise Exception(err)
      ret, err = cifs_unicell.generate_smb_conf()
      if err:
        raise Exception(err)
  
    return django.http.HttpResponseRedirect('/auth_server_settings?ack=edit')
  except Exception, e:
    return_dict['base_template'] = "services_base.html"
    return_dict["page_title"] = 'Modify CIFS authentication method'
    return_dict['tab'] = 'auth_server_settings_tab'
    return_dict["error"] = 'Error modifying CIFS authentication method'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))
  


def save_samba_server_settings(request):

  return_dict = {}
  try:
    if request.method != "POST":
      raise Exception("Invalid access method. Please try again using the menus")
  
    if "security" not in request.POST:
      raise Exception("Invalid security specification. Please try again using the menus")
  
    if request.POST["security"] == "ads":
      form = samba_shares_forms.AuthADSettingsForm(request.POST)
    elif request.POST["security"] == "users":
      form = samba_shares_forms.AuthUsersSettingsForm(request.POST)
    else:
      raise Exception("Invalid security specification. Please try again using the menus")
  
    return_dict["form"] = form
    return_dict["ack"] = "edit"
  
    if form.is_valid():
      cd = form.cleaned_data
      print "Calling auth save settings" 
      ret, err = cifs_common.save_auth_settings(cd)
      print "save settings done"
      if err:
        raise Exception(err)
      if cd["security"] == "ads":
        ret, err = cifs_common.generate_krb5_conf()
        if err:
          raise Exception(err)
      ret, err = cifs_unicell.generate_smb_conf()
      if err:
        raise Exception(err)
      #ret, err = local_users.create_local_user('integralstor_guest', 'IntegralStor_Guest_User', 'integralstorguest')
      # Monkey patch to say skip if user exists. Fix it in integralstor_unicell.cifs
      #if 'The user "integralstor_guest" already exists' in err:
      #  pass
      if cd["security"] == "ads":
        rc, err = cifs_unicell.kinit("administrator", cd["password"], cd["realm"])
        if err:
          raise Exception(err)
        rc, err = cifs_unicell.net_ads_join("administrator", cd["password"], cd["password_server"])
        if err:
          raise Exception(err)
      ret, err = cifs_unicell.reload_configuration()
      if err:
        raise Exception(err)
      #print '6'
    else:
      return django.shortcuts.render_to_response('edit_samba_server_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
  
    #print '7'
    audit_str = "Modified share authentication settings"
    audit.audit("modify_samba_settings", audit_str, request.META)
    return_dict["form"] = form
    return_dict["ack_message"] = "Information successfully updated"
    #print '8'
    return django.http.HttpResponseRedirect('/auth_server_settings?ack=saved')
    #return django.shortcuts.render_to_response('logged_in_error.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "services_base.html"
    return_dict["page_title"] = 'Modify CIFS authentication settings'
    return_dict['tab'] = 'auth_server_settings_tab'
    return_dict["error"] = 'Error modifying CIFS authentication settings'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

