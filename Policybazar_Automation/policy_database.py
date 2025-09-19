import datetime

import psycopg2
from typing import List, Optional
from policy_record import PolicyRecord
from insurance_details import InsuranceDetails
import logging
logger = logging.getLogger(__name__)


class PolicyDatabase:

    @staticmethod
    def get_connection(db_url, db_username, db_password):

        try:

            url_parts = db_url.replace("jdbc:", "").split("//")[1]
            host_port, database = url_parts.split("/")
            host, port = host_port.split(":")

            connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=db_username,
                password=db_password
            )
            logger.info("PostgreSQL Database Connected Successfully!!!")
            return connection
        except Exception:
            logger.info("Database connection failed")
            return None

    @staticmethod
    def get_ids(connection) -> List[int]:

        ids = []
        sql_query = """
        SELECT id FROM policy_bazar_b2b 
        WHERE (registration_number IS NOT NULL AND registration_number NOT IN ('-')) 
        AND liberty_bot_remark = 'pending' 
        AND top_bot_remark = 'pending' 
        AND wishlist_bot_remark = 'pending' 
        ORDER BY id ASC 
        """

        try:
            cursor = connection.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()

            for row in results:
                ids.append(row[0])

            cursor.close()
            return ids

        except Exception:
            logger.info("Error fetching IDs")
            return ids

    @staticmethod
    def get_policy_record(connection, record_id) -> Optional[PolicyRecord]:

        sql_query = """
        SELECT registration_number, ncb, wishlist, add_on 
        FROM policy_bazar_b2b 
        WHERE id = %s
        """

        try:
            cursor = connection.cursor()
            cursor.execute(sql_query, (record_id,))
            result = cursor.fetchone()

            if result:
                return PolicyRecord(
                    record_id,
                    result[0],
                    result[1],
                    result[2],
                    result[3]
                )

            cursor.close()
            return None

        except Exception :
            return None

    @staticmethod
    def fetch_wishlist_name(wishlist_string) -> List[str]:
        wishlist_names = []

        if wishlist_string and wishlist_string.strip():
            insurers = wishlist_string.split(',')
            for insurer in insurers:
                cleaned_name = insurer.strip()
                if cleaned_name:
                    wishlist_names.append(cleaned_name)

        return wishlist_names

    @staticmethod
    def update_ui_error_remarks(connection, record_id):

        sql_query = """
            UPDATE policy_bazar_b2b 
            SET liberty_bot_remark = %s,
                top_bot_remark = %s, 
                wishlist_bot_remark = %s,
                case_end_time = %s
            WHERE id = %s
            """

        try:
            cursor = connection.cursor()
            end_time = datetime.datetime.now().replace(microsecond=0)
            cursor.execute(sql_query,
                           ('UI Error', 'UI Error', 'UI Error', end_time, record_id))
            connection.commit()
            cursor.close()
            logger.info(f"Updated UI Error remarks for ID: {record_id}")

        except Exception :
            logger.info(f"Error updating UI Error remarks for ID {record_id}")
            connection.rollback()

    @staticmethod
    def update_ncb_elements_missing_remark(connection, record_id):

        sql_query = """
             UPDATE policy_bazar_b2b 
             SET liberty_bot_remark = %s,
                 top_bot_remark = %s, 
                 wishlist_bot_remark = %s,
                 case_end_time = %s
             WHERE id = %s
             """

        try:
            cursor = connection.cursor()
            end_time = datetime.datetime.now().replace(microsecond=0)
            cursor.execute(sql_query,
                           ('NCB Error - TP Policy ', 'NCB Error - TP Policy ', 'NCB Error - TP Policy ', end_time, record_id))
            connection.commit()
            cursor.close()
            logger.info(f"Updated NCB elements missing remarks for ID: {record_id}")

        except Exception :
            logger.info(f"Error updating NCB elements missing remarks for ID {record_id}")
            connection.rollback()

    @staticmethod
    def update_new_ui_popup_remarks(connection, record_id):

        sql_query = """
            UPDATE policy_bazar_b2b 
            SET liberty_bot_remark = %s,
                top_bot_remark = %s, 
                wishlist_bot_remark = %s,
                case_end_time = %s
            WHERE id = %s
            """

        try:
            cursor = connection.cursor()
            end_time = datetime.datetime.now().replace(microsecond=0)
            cursor.execute(sql_query,
                           ('Failed: New UI Popup Appears', 'Failed: New UI Popup Appears', 'Failed: New UI Popup Appears', end_time, record_id))
            connection.commit()
            cursor.close()
            logger.info(f"Updated popup failure remarks for ID: {record_id}")

        except Exception :
            logger.info(f"Error updating popup failure for ID {record_id}")
            connection.rollback()

    @staticmethod
    def update_ncb_not_found_remarks(connection, record_id):

        sql_query = """
        UPDATE policy_bazar_b2b 
        SET liberty_bot_remark = %s,
            top_bot_remark = %s, 
            wishlist_bot_remark = %s,
            case_end_time = %s
        WHERE id = %s
        """

        try:
            cursor = connection.cursor()
            end_time = datetime.datetime.now().replace(microsecond=0)
            cursor.execute(sql_query,
                           ('NCB not found on UI', 'NCB not found on UI', 'NCB not found on UI', end_time, record_id))
            connection.commit()
            cursor.close()
            logger.info(f"Updated remarks to 'NCB not found on UI' for ID: {record_id}")
        except Exception :
            logger.info(f"Error updating NCB not found remarks for ID {record_id}")
            connection.rollback()
    @staticmethod
    def update_case_start_time(connection, record_id, start_time):

        sql_query = """
           UPDATE policy_bazar_b2b 
           SET case_start_time = %s 
           WHERE id = %s
           """

        try:
            cursor = connection.cursor()
            clean_start_time = start_time.replace(microsecond=0)
            cursor.execute(sql_query, (clean_start_time, record_id))
            connection.commit()
            cursor.close()
            logger.info(f"Start time updated for ID: {record_id} at {start_time}")
        except Exception :
            logger.info(f"Error updating start time for ID {record_id}")
            connection.rollback()

    @staticmethod
    def update_case_end_time(connection, record_id, end_time):

        sql_query = """
           UPDATE policy_bazar_b2b 
           SET case_end_time = %s 
           WHERE id = %s
           """

        try:
            cursor = connection.cursor()
            clean_end_time = end_time.replace(microsecond=0)
            cursor.execute(sql_query, (clean_end_time, record_id))
            connection.commit()
            cursor.close()
            logger.info(f"End time updated for ID: {record_id} at {end_time}")
        except Exception :
            logger.info(f"Error updating end time for ID {record_id}")
            connection.rollback()

    @staticmethod
    def update_duration(connection, record_id, duration_str):

        sql_query = "UPDATE policy_bazar_b2b SET total_execution_time = %s WHERE id = %s"

        try:
            cursor = connection.cursor()
            cursor.execute(sql_query, (duration_str, record_id))
            connection.commit()
            cursor.close()
            logger.info(f"Duration updated for ID {record_id}: {duration_str}")
        except Exception :
            logger.info(f"Error updating duration for ID {record_id}")
            connection.rollback()


    @staticmethod
    def insert_policy_details(connection, record_id, liberty_details,
                              top1, top2, top3, top4, top5,
                              wishlist1, wishlist2, wishlist3, wishlist4):

        sql_query = """
        UPDATE policy_bazar_b2b SET 
            -- Liberty fields
            insurer_name_liberty = %s, idv_liberty = %s, basic_own_damage_premium_liberty = %s,
            third_party_cover_premium_liberty = %s, zero_depreciation_liberty = %s,
            roadside_assistance_24_7_liberty = %s, engine_protection_cover_liberty = %s,
            consumables_liberty = %s, package_premium_liberty = %s, final_premium_incl_gst_liberty = %s,
            premium_other_addon_autoselected_bundle_liberty = %s, tyre_liberty = %s, gap_cover_liberty = %s, lgi_quote_ranking = %s,

            -- Top 1 fields
            insurer_name_top_1 = %s, idv_top_1 = %s, basic_own_damage_premium_top_1 = %s,
            third_party_cover_premium_top_1 = %s, zero_depreciation_top_1 = %s,
            roadside_assistance_24x7_top_1 = %s, engine_protection_cover_top_1 = %s,
            consumables_top_1 = %s, package_premium_top_1 = %s, final_premium_incl_gst_top_1 = %s,
            premium_other_addon_autoselected_bundle_top_1 = %s, tyre_top_1 = %s, gap_cover_top_1 = %s,

            -- Top 2 fields
            insurer_name_top_2 = %s, idv_top_2 = %s, basic_own_damage_premium_top_2 = %s,
            third_party_cover_premium_top_2 = %s, zero_depreciation_top_2 = %s,
            roadside_assistance_24x7_top_2 = %s, engine_protection_cover_top_2 = %s,
            consumables_top_2 = %s, package_premium_top_2 = %s, final_premium_incl_gst_top_2 = %s,
            premium_other_addon_autoselected_bundle_top_2 = %s, tyre_top_2 = %s, gap_cover_top_2 = %s,

            -- Top 3 fields
            insurer_name_top_3 = %s, idv_top_3 = %s, basic_own_damage_premium_top_3 = %s,
            third_party_cover_premium_top_3 = %s, zero_depreciation_top_3 = %s,
            roadside_assistance_24x7_top_3 = %s, engine_protection_cover_top_3 = %s,
            consumables_top_3 = %s, package_premium_top_3 = %s, final_premium_incl_gst_top_3 = %s,
            premium_other_addon_autoselected_bundle_top_3 = %s, tyre_top_3 = %s, gap_cover_top_3 = %s,

            -- Top 4 fields
            insurer_name_top_4 = %s, idv_top_4 = %s, basic_own_damage_premium_top_4 = %s,
            third_party_cover_premium_top_4 = %s, zero_depreciation_top_4 = %s,
            roadside_assistance_24x7_top_4 = %s, engine_protection_cover_top_4 = %s,
            consumables_top_4 = %s, package_premium_top_4 = %s, final_premium_incl_gst_top_4 = %s,
            premium_other_addon_autoselected_bundle_top_4 = %s, tyre_top_4 = %s, gap_cover_top_4 = %s,

            -- Top 5 fields
            insurer_name_top_5 = %s, idv_top_5 = %s, basic_own_damage_premium_top_5 = %s,
            third_party_cover_premium_top_5 = %s, zero_depreciation_top_5 = %s,
            roadside_assistance_24x7_top_5 = %s, engine_protection_cover_top_5 = %s,
            consumables_top_5 = %s, package_premium_top_5 = %s, final_premium_incl_gst_top_5 = %s,
            premium_other_addon_autoselected_bundle_top_5 = %s, tyre_top_5 = %s, gap_cover_top_5 = %s,

            -- Wishlist 1 fields
            insurer_name_wishlist_1 = %s, idv_wishlist_1 = %s, basic_own_damage_premium_wishlist_1 = %s,
            third_party_cover_premium_wishlist_1 = %s, zero_depreciation_wishlist_1 = %s,
            roadside_assistance_24x7_wishlist_1 = %s, engine_protection_cover_wishlist_1 = %s,
            consumables_wishlist_1 = %s, package_premium_wishlist_1 = %s, final_premium_incl_gst_wishlist_1 = %s,
            premium_other_addon_autoselected_bundle_wishlist_1 = %s, tyre_wishlist_1 = %s, gap_cover_wishlist_1 = %s,

            -- Wishlist 2 fields
            insurer_name_wishlist_2 = %s, idv_wishlist_2 = %s, basic_own_damage_premium_wishlist_2 = %s,
            third_party_cover_premium_wishlist_2 = %s, zero_depreciation_wishlist_2 = %s,
            roadside_assistance_24x7_wishlist_2 = %s, engine_protection_cover_wishlist_2 = %s,
            consumables_wishlist_2 = %s, package_premium_wishlist_2 = %s, final_premium_incl_gst_wishlist_2 = %s,
            premium_other_addon_autoselected_bundle_wishlist_2 = %s, tyre_wishlist_2 = %s, gap_cover_wishlist_2 = %s,

            -- Wishlist 3 fields
            insurer_name_wishlist_3 = %s, idv_wishlist_3 = %s, basic_own_damage_premium_wishlist_3 = %s,
            third_party_cover_premium_wishlist_3 = %s, zero_depreciation_wishlist_3 = %s,
            roadside_assistance_24x7_wishlist_3 = %s, engine_protection_cover_wishlist_3 = %s,
            consumables_wishlist_3 = %s, package_premium_wishlist_3 = %s, final_premium_incl_gst_wishlist_3 = %s,
            premium_other_addon_autoselected_bundle_wishlist_3 = %s, tyre_wishlist_3 = %s, gap_cover_wishlist_3 = %s,

            -- Wishlist 4 fields
            insurer_name_wishlist_4 = %s, idv_wishlist_4 = %s, basic_own_damage_premium_wishlist_4 = %s,
            third_party_cover_premium_wishlist_4 = %s, zero_depreciation_wishlist_4 = %s,
            roadside_assistance_24x7_wishlist_4 = %s, engine_protection_cover_wishlist_4 = %s,
            consumables_wishlist_4 = %s, package_premium_wishlist_4 = %s, final_premium_incl_gst_wishlist_4 = %s,
            premium_other_addon_autoselected_bundle_wishlist_4 = %s, tyre_wishlist_4 = %s, gap_cover_wishlist_4 = %s,

            -- Bot remarks
            liberty_bot_remark = 'completed', top_bot_remark = 'completed', wishlist_bot_remark = 'completed',
            case_end_time = %s WHERE id = %s
        """

        try:
            cursor = connection.cursor()

            end_time = datetime.datetime.now().replace(microsecond=0)

            params = []

            params.extend(PolicyDatabase._get_insurer_params(liberty_details))

            if liberty_details and hasattr(liberty_details, 'ranking'):
                params.append(liberty_details.ranking)
            else:
                params.append(None)

            for details in [top1, top2, top3, top4, top5,
                            wishlist1, wishlist2, wishlist3, wishlist4]:
                params.extend(PolicyDatabase._get_insurer_params(details))

            params.append(end_time)
            params.append(record_id)

            cursor.execute(sql_query, params)
            connection.commit()

            if cursor.rowcount > 0:
                logger.info(f"Policy updated successfully for ID: {record_id}")
            else:
                logger.info(f"Update failed for ID: {record_id}")

            cursor.close()

        except Exception:
            logging.info(f"Error updating policy for ID: {record_id}",exc_info=True)
            connection.rollback()

    @staticmethod
    def _get_insurer_params(details: Optional[InsuranceDetails]) -> List[Optional[str]]:

        if details is None:
            return [None] * 13

        return [
            getattr(details, 'insurer', None),
            getattr(details, 'carvalue', None),
            getattr(details, 'damage', None),
            getattr(details, 'third_party_cover_premium', None),
            getattr(details, 'zero_depreciation', None),
            getattr(details, 'roadside', None),
            getattr(details, 'engine_protection_cover', None),
            getattr(details, 'consumables', None),
            getattr(details, 'package_premium', None),
            getattr(details, 'premium', None),
            getattr(details, 'premium_other_addon_autoselected_bundle', None),
            getattr(details, 'tyre', None),
            getattr(details, 'gap_cover', None)
        ]