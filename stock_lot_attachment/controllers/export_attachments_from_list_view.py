
import logging
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
import zipfile
from datetime import datetime
from odoo import http
from odoo.http import request
from odoo.http import content_disposition
import ast

_logger = logging.getLogger(__name__)


class Binary(http.Controller):

    @http.route('/web/binary/download_document', type='http', auth="public")
    def download_document(self, move_line_ids=None, **kw):

        move_line_ids = ast.literal_eval(move_line_ids)
        move_lines = request.env['stock.move.line'].browse(move_line_ids)

        bitIO = BytesIO()
        zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)

        for line in move_lines:
            for attachment in line.attachment_ids:

                file_store = attachment.store_fname
                if not file_store:
                    continue

                file_path = attachment._full_path(file_store)

                file_name = (
                    f"{line.so_no} - "
                    f"{line.quantity} "
                    f"{line.product_uom_id.name} - "
                    f"{attachment.name}"
                )

                zip_file.write(file_path, file_name)

        zip_file.close()

        zip_filename = "%s.zip" % datetime.now()

        return request.make_response(
            bitIO.getvalue(),
            headers=[
                ('Content-Type', 'application/x-zip-compressed'),
                ('Content-Disposition', content_disposition(zip_filename))
            ]
        )
