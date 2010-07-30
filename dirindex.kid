<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
import os.path
import webdav
import davutils
import urllib
?>
<html xmlns:py="http://purl.org/kid/ns#" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Index for ${urllib.unquote(real_url)}</title>
    <style type="text/css">
        tr:nth-child(even) {background-color: #CCE;}
        tr:nth-child(odd) {background-color: #EEE;}
        td {padding-right: 2em;}
        th, table {border-bottom: 1px solid black;}
        td.size {text-align: right;}
        .message {font-weight: bold;}
    </style>
</head>
<body>
    <h1>Index for ${urllib.unquote(real_url)}</h1>
    <p>Mount this directory using WebDAV with url <a href="${real_url}">${real_url}</a>.</p>

    <h2>Upload a file</h2>
    <p>
    <form action="#" method="post" enctype="multipart/form-data">
        <input type="file" name="file" size="50" />
        <input type="submit" value="Upload"
            onclick="document.forms[0].submit();this.disabled=true" />
    </form>
    </p>

    <p class="message" py:if="message" py:content="message" />

    <h2>Current files</h2>
    <form action="#" method="post">
    <table>
    <tr><th>Filename</th><th>Last modified</th><th>Size</th><th>Type</th><th>Select</th></tr>
    <tr py:if="has_parent">
        <td><a href="../">..</a></td>
        <td>&nbsp;</td>
        <td class="size"></td>
        <td>Directory</td>
        <td></td>
    </tr>
    <tr py:for="filename in files">
        <?python file_path = os.path.join(real_path, filename) ?>
        <td><a href="${real_url + filename}">${filename}</a></td>
        <td>${davutils.get_usertime(os.path.getmtime(file_path))}</td>
        <td class="size" py:if="not os.path.isdir(file_path)">
            ${davutils.pretty_unit(os.path.getsize(file_path), 1024, 0, '%0.2f') + 'B'}
        </td>
        <td class="size" py:if="os.path.isdir(file_path)"></td>
        <td py:if="not os.path.isdir(file_path)"></td>
        <td py:if="os.path.isdir(file_path)">Directory</td>
        <td><input type="checkbox" name="select" value="${filename}" /></td>
    </tr>
    </table>
    <p>
        <input type="submit" name="btn_remove" value="Remove selected"
            onclick="return confirm('Really remove files?')"/>
        <input type="submit" name="btn_download" value="Download selected" />
    </p>
    </form>

    <p>Index listing generated by ${webdav.__program_name__} ${webdav.__version__}.</p>
</body>
</html>