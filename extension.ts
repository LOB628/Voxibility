// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';
// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "helloworld" is now active!');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	let disposable = vscode.commands.registerCommand('helloworld.helloWorld', () => {
        const extensionPath = context.extensionPath;
        const pythonScriptPath = path.join(extensionPath, 'voxbasic.py');
        const pythonExecutable = 'python'; // Change this if python command is not in PATH

        const command = `${pythonExecutable} ${pythonScriptPath}`;
        child_process.exec(command, (error, stdout, stderr) => {
            if (error) {
                vscode.window.showErrorMessage(`Error running Python script: ${error.message}`);
                return;
            }
            if (stderr) {
                vscode.window.showErrorMessage(`Python script stderr: ${stderr}`);
                return;
            }
            vscode.window.showInformationMessage(`Python script output: ${stdout}`);
        });
    });

	context.subscriptions.push(disposable);
}
