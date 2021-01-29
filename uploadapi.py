"""
implements UploadAPIHandler that handles post requests for
api endpoints /delete /upload /download

runs HTTPServer on a localhost not as a daemon if executed.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import re
import errno
import cgi
import hashlib

C_ROOT_FOLDER = "/home/nuser/Documents/0x428a2f98"  # constant for dubuging


def md5(data):
    """Uses <hashlib> to get md5 file hash

    Args: 
        data (bytes): file data

    Returns:
        [str]: md5 checksum
    """
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()


def generate_dubug_html():
    """Generates POST submit forms for api endpoints and uploaded files hash list html.

    Returns:
        [bytes]: encoded html fragment
    """
    response_data = b"""<form enctype="multipart/form-data" method="post" action="upload">
                <p>Upload File: <input type="file" name="file"></p>
                <p><input type="submit" value="Upload"></p>
                </form>"""
    response_data += b"""<form enctype="multipart/form-data" method="post" action="delete">
                <p>Delete : <input type="text" name="file"></p>
                <p><input type="submit" value="Delete"></p>
                </form>"""
    response_data += b"""<form enctype="multipart/form-data" method="post" action="download">
                <p>Download : <input type="text" name="file"></p>
                <p><input type="submit" value="Download"></p>
                </form>"""

    response_data += b"<div> Files:"
    storedirpath = C_ROOT_FOLDER + "/store/"
    makedir_to_path(storedirpath)
    for parent_folder in os.listdir(storedirpath):
        for hash_folder in os.listdir(storedirpath + parent_folder):
            response_data += b"<p>"
            response_data += hash_folder.encode()
            response_data += b"</p>"
    response_data += b"</div>"

    return response_data


def makedir_to_path(dirpath):
    """Creates directories if they don't exists. Handles shared access.

    Args:
            dirpath ([type]): post form data
    """
    if not os.path.exists(os.path.dirname(dirpath)):
        try:
            os.makedirs(os.path.dirname(dirpath))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


class UploadAPIHandler(BaseHTTPRequestHandler):
    """Extends BaseHTTPRequestHandler and implements do_GET and do_POST.

    Upload api endpoints are accessible by post requests.
    Get requests provide response with a debug information html.
    """

    def upload_endpoint(self, form):
        """Generates md5 hash for an uploaded file and stores file
        in a /store/parentfoldername = 1st 2 letters of a file hash
        and /store/parentfoldername/foldername = file hash

        Args:
            form (cgi.FieldStorage): request data from parse_post_data()

        Returns:
            [bytes]: generated html response fragment
        """
        pattern = re.compile("[^A-z0-9_.]+|\.(?=.*\.)", re.UNICODE)

        try:
            data = form['file'].file.read()
            tmp_md = md5(data)
            dirpath = C_ROOT_FOLDER + "/store/" + \
                tmp_md[:2] + "/" + tmp_md + "/"
            makedir_to_path(dirpath)

            filename = pattern.sub("", form['file'].filename)
            with open(dirpath + filename, "wb") as fw:
                fw.write(data)

            response_data = b"upload endpoint. </br> file md5 hash: ["
            response_data += (tmp_md).encode()
            response_data += b"]"
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        except AttributeError:
            response_data = "Upload ERROR"
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        return response_data

    def delete_endpoint(self, form):
        """Checks for a file stored in an inputed hash folder, deletes file
        & folder if files are found.

        Args:
            form (cgi.FieldStorage): request data from parse_post_data()

        Returns:
            [bytes]: generated html response fragment
        """
        pattern = re.compile("[\W_]+", re.UNICODE)
        tmp_hash = pattern.sub("", form.getfirst("file"))

        if not len(tmp_hash) == 32:
            response_data = b"Delete ERROR"
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        else:
            parent_folder = tmp_hash[:2]
            hash_folder = tmp_hash
            dirpath = C_ROOT_FOLDER + "/store/" + parent_folder + "/" + hash_folder + "/"

            try:
                filename = os.listdir(dirpath)[0]
                response_data = filename.encode()
                response_data += b" file deleted. "
                os.remove(dirpath + filename)

                os.rmdir(dirpath)
                response_data += ("/store/" + parent_folder + "/" + hash_folder + "/").encode()
                response_data += b" folder deleted."
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
            except FileNotFoundError:
                response_data = b"Delete ERROR"
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

        return response_data

    def download_endpoint(self, form):
        """Checks for a file stored in an inputed hash folder, returns file
        & sets atachment header if file is found.

        Args:
            form (cgi.FieldStorage): request data from parse_post_data()

        Returns:
            [bytes]: generated html response fragment
        """
        pattern = re.compile("[\W_]+", re.UNICODE)
        tmp_hash = pattern.sub("", form.getfirst("file"))
        if not len(tmp_hash) == 32:
            response_data = b"Download ERROR"
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        else:
            parent_folder = tmp_hash[:2]
            hash_folder = tmp_hash
            dirpath = C_ROOT_FOLDER + "/store/" + parent_folder + "/" + hash_folder + "/"

            try:
                filename = os.listdir(dirpath)[0]
                with open(dirpath + filename, "rb") as rf:
                    response_data = rf.read()
                self.send_response(200)
                self.send_header("Content-Disposition",
                                    'attachment; filename="%s"' % filename)
                self.end_headers()
            except FileNotFoundError:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                response_data = b"Download ERROR"

        return response_data

    def parse_post_data(self, verbose=0):
        """Uses standart cgi lib to parse request data & return this
        and optionaly generates dubug html fragment.

        Args:
            verbose (int, optional): If True generates info_html else returns empty
            placeholder. Defaults to 0.

        Returns:
            dict(): {form = request data, info_html = generated html with request data}
        """
        request_form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type'],
                     })
        if verbose:
            response_data = b"</br> post data: ["
            for i_key in request_form:
                response_data += b" %"
                response_data += i_key.encode()
                response_data += b": "
                tmp_args = "".join(request_form.getlist(i_key))
                response_data += tmp_args.encode()
            response_data += b" ]"
            return dict(form=request_form, info_html=response_data)

        return dict(form=request_form, info_html=b"")

    def do_GET(self):
        """Serve GET request. Display submit forms and uploaded file list on root path for easy debuging.
        """
        response_data = b"""<html><body>
                    GET method evoked
                    ver 0.3
                    </br>"""

        if self.path == '/':
            response_data += generate_dubug_html()

        response_data += b"""</body></html>"""

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(response_data))

    def do_POST(self):
        """Serve POST request. Depending on endpoint route to upload, delete or download.
        """

        if self.path == '/upload':
            post_info = self.parse_post_data()
            response_data = self.upload_endpoint(post_info['form'])

        if self.path == '/delete':
            post_info = self.parse_post_data(verbose=True)
            response_data = self.delete_endpoint(post_info['form'])

        if self.path == '/download':
            post_info = self.parse_post_data(verbose=True)
            response_data = self.download_endpoint(post_info['form'])

        self.wfile.write(bytes(response_data))


if __name__ == "__main__":
    # runs HTTPServer on a localhost not as a daemon
    Handler = UploadAPIHandler

    httpd = HTTPServer(("localhost", 5050), Handler)
    httpd.serve_forever()
