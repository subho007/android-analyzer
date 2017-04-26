import logging
import re
import subprocess
import time

from com.dtmilano.android.viewclient import ViewClient
from src.models.settings import Settings
from src.models.smart_input_assignments import SmartInputAssignment

from src.analysis.environment import device_manager
from src.analysis.environment.certificate_installation import install_as_system_certificate
from src.analysis.environment.mitm_proxy import start_mitm_proxy, kill_mitm_proxy
from src.definitions import INPUT_APK_DIR, LOGS_DIR
from src.services.scenario_settings_service import get_all_enabled_of_user

logger = logging.getLogger(__name__)


class DynamicAnalysisResult:
    # if no dynamic analysis was run, log_id should not be set
    def __init__(self, scenario, log_id=None):
        self.scenario = scenario
        self.log_id = log_id

    def has_been_run(self):
        return self.log_id

    def is_statically_vulnerable(self):
        return self.scenario.is_statically_vulnerable()

    def get_mitm_proxy_log(self):
        return LOGS_DIR + "mitm_proxy_log" + str(self.log_id)

    def get_network_monitor_log(self):
        return LOGS_DIR + "network_monitor_log" + str(self.log_id)


def analyze_dynamically(apk_name, static_analysis_results, smart_input_results):
    dynamic_analysis_results = []

    # ==== Setup ====
    emulator_id = device_manager.get_emulator()
    apk_path = INPUT_APK_DIR + apk_name + ".apk"

    install_apk(emulator_id, apk_path)

    start_app(emulator_id, static_analysis_results.package)
    # ==== ===== ====

    time.sleep(1)

    smart_input_assignment = SmartInputAssignment()

    log_id = 0
    scenario_settings = get_all_enabled_of_user()
    scenarios, solved_scenarios = Settings(scenario_settings).get_scenarios(static_analysis_results)

    for scenario in scenarios:
        log_id += 1
        dynamic_analysis_results += run_scenario(
            scenario,
            log_id,
            emulator_id,
            smart_input_results,
            smart_input_assignment)

    # ==== Shutdown ====
    uninstall_apk(emulator_id, static_analysis_results.package)
    # ==== ======== ====

    dynamic_analysis_results += [DynamicAnalysisResult(solved_scenario) for solved_scenario in solved_scenarios]

    return dynamic_analysis_results


def run_scenario(scenario, log_id, emulator_id, smart_input_results, smart_input_assignment):
    logger.debug("Checking for vulnerable " + scenario.scenario_settings.vuln_type.value + " implementations")

    # ==== Setup ====
    if scenario.scenario_settings.sys_certificates:
        for sys_certificate in scenario.scenario_settings.sys_certificates:
            install_as_system_certificate(emulator_id, sys_certificate)

    mitm_proxy_process = start_mitm_proxy(
        scenario.scenario_settings.mitm_certificate,
        scenario.scenario_settings.add_upstream_certs,
        log_id)

    # network_monitor_process = start_network_monitor(emulator_id, static_analysis_results.package, log_id)
    # ==== ===== ====

    run_ui_traversal(scenario, emulator_id, smart_input_results, smart_input_assignment)

    time.sleep(5)  # wait before shutting down mitmproxy since there might be a last request caused by ui traversal

    # ==== Shutdown ====
    # kill_network_monitor(network_monitor_process)
    kill_mitm_proxy(mitm_proxy_process)
    # ==== ======== ====

    return [DynamicAnalysisResult(scenario, log_id)]


def run_ui_traversal(scenario, emulator_id, smart_input_results, smart_input_assignment):
    smart_input_for_activity = smart_input_results[scenario.activity_name]

    # reset the window, press enter two times
    press_enter(emulator_id)
    press_enter(emulator_id)

    start_activity(emulator_id, scenario.activity_name)

    time.sleep(5)  # wait for starting activity

    device, serialno = ViewClient.connectToDeviceOrExit(serialno=emulator_id)
    vc = ViewClient(device, serialno)

    edittexts = vc.findViewsWithAttribute("class", "android.widget.EditText")
    logger.info("EditText views: %s" % str(edittexts))
    clickable_views = vc.findViewsWithAttribute("clickable", "true")
    logger.info("Clickable views: %s" % str(clickable_views))
    listviews = vc.findViewsWithAttribute("class", "android.widget.ListView")
    logger.info("ListViews: %s" % str(listviews))

    fill_edit_texts(edittexts, smart_input_for_activity, smart_input_assignment, vc, emulator_id)

    click_clickable_views(clickable_views, vc, device, emulator_id)

    # TODO: listviews


def fill_edit_texts(edittexts, smart_input_for_activity, smart_input_assignment, vc, emulator_id):
    for edittext in edittexts:
        fill_edit_text(edittext, smart_input_for_activity, smart_input_assignment, vc, emulator_id)


def fill_edit_text(edittext, smart_input_for_activity, smart_input_assignment, vc, emulator_id):
    smart_input = get_smart_input_for_edittext(
        edittext.getId(),
        smart_input_for_activity,
        smart_input_assignment)
    logger.info("Smart input for EditText: " + smart_input + ", " + repr(edittext))
    edittext.touch()
    edittext.setText(smart_input)
    if vc.isKeyboardShown():
        press_back(emulator_id)


def click_clickable_views(clickable_views, vc, device, emulator_id):
    clickable_views_wo_edittexts = [c for c in clickable_views if c.getClass() != 'android.widget.EditText']
    for clickable_view in clickable_views_wo_edittexts:
        old_window = device.getFocusedWindowName()

        logger.info("Clicking on view: " + repr(clickable_view))
        clickable_view.touch()

        time.sleep(2)

        if vc.isKeyboardShown():
            press_back(emulator_id)

        new_window = device.getFocusedWindowName()
        if new_window != old_window:
            logger.warn("Focused window changed while clicking view. Pressing back button.")
            press_back(emulator_id)

            time.sleep(5)

            new_window = device.getFocusedWindowName()
            if new_window != old_window:
                logger.warn("Did not return to old focused window after pressing back button. Trying enter.")
                press_enter(emulator_id)
                press_enter(emulator_id)
                if new_window != old_window:
                    logger.warn("Did not return to old focused window after pressing enter.")
                    break


def install_apk(emulator_id, apk_path):
    cmd = "adb -s " + emulator_id + " install " + apk_path
    logger.debug(cmd)
    subprocess.check_call(cmd, shell=True)


def start_app(emulator_id, package_name):
    cmd = "adb -s " + emulator_id + " shell monkey -p " + package_name + " 1"
    logger.debug(cmd)
    subprocess.check_call(cmd, shell=True)


def press_enter(emulator_id):
    cmd = "adb -s " + emulator_id + " shell input keyevent 66"
    logger.debug(cmd)
    subprocess.check_call(cmd, shell=True)


def start_activity(emulator_id, meth_nm):
    last_dot = meth_nm.rindex('.')
    component_name = meth_nm[:last_dot] + "/" + meth_nm[last_dot:]
    cmd = "adb -s " + emulator_id + " shell am start -n " + component_name
    logger.debug(cmd)
    subprocess.check_call(cmd, shell=True)


def uninstall_apk(emulator_id, package_name):
    cmd = "adb -s " + emulator_id + " uninstall " + package_name
    logger.debug(cmd)
    subprocess.check_call(cmd, shell=True)


def press_back(emulator_id):
    cmd = "adb -s " + emulator_id + " shell input keyevent 4"
    logger.debug(cmd)
    subprocess.check_call(cmd, shell=True)


def get_smart_input_for_edittext(edittext_id, smart_input_for_activity, smart_input_ass):
    edittext_name = re.match(".*id/(.*)$", edittext_id).group(1)

    for text_field in smart_input_for_activity:
        if text_field.name == edittext_name:
            type_class = text_field.get_type_class()
            if type_class:
                type_variation = text_field.get_type_variation(type_class)
                if type_variation:
                    return smart_input_ass.type_variation_ass[type_variation]
                else:
                    return smart_input_ass.type_class_ass[text_field.get_type_class()]
    return None  # TODO: what to do here?

