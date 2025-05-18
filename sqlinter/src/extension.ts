import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';


const execAsync = promisify(exec);
let decorationType: vscode.TextEditorDecorationType;

export function activate(context: vscode.ExtensionContext) {
    const extensionRootPath = context.extensionUri.fsPath;
    console.log('Congratulations, your extension "sqlinter" is now active!');
    console.log(`путь к расширению: ${extensionRootPath}`);

    decorationType = vscode.window.createTextEditorDecorationType({
        backgroundColor: 'rgba(100, 200, 100, 0.2)',
        border: '1px solid rgba(100, 200, 100, 0.7)'
    });

	//обработка сохранения
const saveDisposable = vscode.workspace.onDidSaveTextDocument(async (document) => {
    const absoluteFilePath = document.fileName; //абсолютный путь к файлу
    console.log(`Обработан файл: ${absoluteFilePath}`);
    
    if (document.languageId === 'python' || document.fileName.endsWith('.py')) {
        try {
            const sqlQueries = await runPythonScript(extensionRootPath, absoluteFilePath);
            console.log(sqlQueries);
            await highlightSqlQueries(document, sqlQueries);
            vscode.window.showInformationMessage(`Обработан файл: ${absoluteFilePath}`);
        } catch (error) {
            vscode.window.showErrorMessage(`Ошибка обработки ${absoluteFilePath}: ${error}`);
        }
    }
});

    // Добавляем в подписки для очистки при деактивации
    context.subscriptions.push(saveDisposable);

    //базовый хеллоу ворлд
    const disposable = vscode.commands.registerCommand('sqlinter.helloWorld', () => {
		console.log('Hello World from SQLinter!');
        vscode.window.showInformationMessage('Hello World from SQLinter!');
    });
    context.subscriptions.push(disposable);
}

async function runPythonScript(rootPath: string, filePath: string) {
    // Получаем путь к директории с расширением
    const extensionDir = rootPath;
    
    // Формируем путь к Python-скрипту в той же директории
    const pythonScriptPath = path.join(extensionDir, 'scripts/main.py'); 
    console.log(`запущен скрипт: ${pythonScriptPath}`);
    const command = `python "${pythonScriptPath}" "${filePath}"`;
    
    const { stdout, stderr } = await execAsync(command, {encoding: 'utf-8'});
    
    const outputChannel = vscode.window.createOutputChannel('Python Output');


    outputChannel.appendLine(stdout);
    if (stderr) outputChannel.appendLine(`Ошибки: ${stderr}`);
    outputChannel.show();
    // console.log(`питон аутпут: ${stdout}`);
    try {
        
        // Парсим JSON
        const result = JSON.parse(stdout);
        // console.log(result);
        if (result.error) {
            throw new Error(result.error);
        }

        // result теперь содержит массив SQL-запросов
        return result as Array<{
            query: string;
            verdict: string;
            reason: string;
            start: number;
            end: number;
        }>;


    } catch (error) {
        vscode.window.showErrorMessage(`Ошибка парсинга SQL: ${error}`);
        return [];
    }
}

async function highlightSqlQueries(document: vscode.TextDocument, extractedQueries: any[]) {
    decorationType.dispose();
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('sql-queries');
    diagnosticCollection.clear();

    try {
        // 1. Запускаем Python-скрипт
        const queries = extractedQueries;

        // 2. Создаем декорации для подсветки
        const decorations: vscode.DecorationOptions[] = [];
        decorationType = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(100, 200, 100, 0.2)',
            border: '1px solid rgba(100, 200, 100, 0.7)',
            borderRadius: '2px'
        });

        // 3. Преобразуем позиции
        queries.forEach((query: any) => {
            const startPos = document.positionAt(query.start);
            const endPos = document.positionAt(query.end);
            
            decorations.push({
                range: new vscode.Range(startPos, endPos),
                hoverMessage: 'SQL запрос: ' + query.query
            });
        });

        // 4. Применяем подсветку
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            editor.setDecorations(decorationType, decorations);
        }

    } catch (error) {
        vscode.window.showErrorMessage(`Ошибка анализа SQL: ${error}`);
    }
}



export function deactivate() {}

