
import django.template, django, shutil
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from integralstor_common import ntp, services_management
from integralstor_unicell import system_info

import integral_view
from integral_view.forms import common_forms
from integral_view.utils import iv_logging

@login_required
def view_ntp_settings(request):
  return_dict = {}
  try:
    ntp_servers, err = ntp.get_ntp_servers()
    if err:
      raise Exception(err)
    return_dict["ntp_servers"] = ntp_servers
    if "ack" in request.REQUEST and request.REQUEST['ack'] == 'saved':
      return_dict["ack_message"] = 'NTP settings have successfully been updated.'
    return django.shortcuts.render_to_response('view_ntp_settings.html', return_dict, context_instance=django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "system_base.html"
    return_dict["page_title"] = 'View NTP settings'
    return_dict['tab'] = 'ntp_settings_tab'
    return_dict["error"] = 'Error retrieving NTP settings'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

@login_required
def configure_ntp_settings(request):

  return_dict = {}
  try:
    if request.method=="GET":
      ntp_servers, err = ntp.get_ntp_servers()
      if err:
        raise Exception(err)
      if not ntp_servers:
        form = common_forms.ConfigureNTPForm()
      else:
        form = common_forms.ConfigureNTPForm(initial={'server_list': ','.join(ntp_servers)})
      url = "edit_ntp_settings.html"
    else:
      form = common_forms.ConfigureNTPForm(request.POST)
      if form.is_valid():
        iv_logging.debug("Got valid request to change NTP settings")
        cd = form.cleaned_data
        si, err = system_info.load_system_config()
        if err:
          raise Exception(err)
        server_list = cd["server_list"]
        if ',' in server_list:
          slist = server_list.split(',')
        else:
          slist = server_list.split(' ')
        with open('/tmp/ntp.conf', 'w') as temp:
          #First create the ntp.conf file for the primary and secondary nodes
          temp.write("driftfile /var/lib/ntp/drift\n")
          temp.write("restrict default kod nomodify notrap nopeer noquery\n")
          temp.write("restrict -6 default kod nomodify notrap nopeer noquery\n")
          temp.write("logfile /var/log/ntp.log\n")
          temp.write("\n")
          for server in slist:
            temp.write("server %s iburst\n"%server)
          temp.flush()
          temp.close()
        shutil.move('/tmp/ntp.conf', '/etc/ntp.conf')
        #ret, err = ntp.restart_ntp_service()
        ret, err = services_management.change_service_status('ntpd', 'restart')
        if err:
          raise Exception(err)
        return django.http.HttpResponseRedirect("/view_ntp_settings?ack=saved")
      else:
        #invalid form
        iv_logging.debug("Got invalid request to change NTP settings")
        url = "edit_ntp_settings.html"
    return_dict["form"] = form
    return django.shortcuts.render_to_response(url, return_dict, context_instance = django.template.context.RequestContext(request))
  except Exception, e:
    return_dict['base_template'] = "system_base.html"
    return_dict["page_title"] = 'Modify NTP notifications settings'
    return_dict['tab'] = 'ntp_settings_tab'
    return_dict["error"] = 'Error modifying NTP notifications settings'
    return_dict["error_details"] = str(e)
    return django.shortcuts.render_to_response("logged_in_error.html", return_dict, context_instance=django.template.context.RequestContext(request))

